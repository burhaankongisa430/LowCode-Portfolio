"""
Azure Active Directory & Microsoft 365 provisioner.
Creates the new hire's work account, assigns licenses, sets manager,
and adds them to department security groups — all before Day 1.

Uses MSAL client credentials flow (app-only permissions):
  - User.ReadWrite.All
  - Directory.ReadWrite.All
  - GroupMember.ReadWrite.All
"""

import logging
import re
import requests
import msal
from config import Config

log = logging.getLogger(__name__)
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _get_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=Config.GRAPH_CLIENT_ID,
        client_credential=Config.GRAPH_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{Config.GRAPH_TENANT_ID}",
    )
    result = app.acquire_token_for_client(scopes=Config.GRAPH_SCOPES)
    if "access_token" not in result:
        raise RuntimeError(f"MSAL token error: {result.get('error_description', 'unknown')}")
    return result["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _graph(method: str, path: str, token: str, body: dict = None) -> dict | None:
    url = f"{GRAPH_BASE}/{path.lstrip('/')}"
    r = requests.request(method, url, headers=_headers(token), json=body, timeout=15)
    if r.status_code == 204:
        return None
    r.raise_for_status()
    return r.json()


def _build_upn(first_name: str, last_name: str) -> str:
    """Generate a work email from the hire's name. Handles duplicates with a suffix."""
    clean = re.sub(r"[^a-z]", "", f"{first_name}{last_name}".lower())
    return f"{clean}@{Config.AD_DOMAIN}"


def _find_manager_object_id(manager_email: str, token: str) -> str | None:
    """Look up the manager's Azure AD object ID by email."""
    try:
        result = _graph("GET", f"users/{manager_email}", token)
        return result.get("id")
    except requests.HTTPError:
        log.warning("Could not find manager in Azure AD: %s", manager_email)
        return None


def _get_department_group_id(department: str, token: str) -> str | None:
    """Find the Azure AD security group for a department by display name."""
    try:
        result = _graph("GET", f"groups?$filter=displayName eq '{department} - All'&$select=id", token)
        groups = result.get("value", [])
        return groups[0]["id"] if groups else None
    except requests.HTTPError:
        log.warning("Could not find AD group for department: %s", department)
        return None


def provision_new_hire(hire: dict) -> dict:
    """
    Full provisioning pipeline for a new hire.

    hire keys required: firstName, lastName, jobTitle, department,
                        employmentType, managerEmail, employeeId

    Returns:
        {
            "success": bool,
            "workEmail": str,
            "adObjectId": str,
            "licenseAssigned": bool,
            "managerSet": bool,
            "groupAdded": bool,
            "errors": list
        }
    """
    result = {
        "success":        False,
        "workEmail":      "",
        "adObjectId":     "",
        "licenseAssigned":False,
        "managerSet":     False,
        "groupAdded":     False,
        "errors":         [],
    }

    try:
        token = _get_token()
    except RuntimeError as exc:
        result["errors"].append(f"Token acquisition failed: {exc}")
        return result

    upn = _build_upn(hire["firstName"], hire["lastName"])
    result["workEmail"] = upn

    # Step 1: Create the user account
    user_body = {
        "accountEnabled":    False,  # disabled until Day 1
        "displayName":       f"{hire['firstName']} {hire['lastName']}",
        "givenName":         hire["firstName"],
        "surname":           hire["lastName"],
        "mailNickname":      upn.split("@")[0],
        "userPrincipalName": upn,
        "jobTitle":          hire.get("jobTitle", ""),
        "department":        hire.get("department", ""),
        "employeeId":        hire.get("employeeId", ""),
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": f"Welcome1!{hire.get('employeeId', 'Temp')}"
        },
        "usageLocation": "ZA",
    }

    try:
        user = _graph("POST", "users", token, user_body)
        result["adObjectId"] = user["id"]
        log.info("Created AD account: %s (objectId: %s)", upn, user["id"])
    except requests.HTTPError as exc:
        result["errors"].append(f"User creation failed: {exc}")
        return result

    object_id = result["adObjectId"]

    # Step 2: Assign M365 license
    sku_id = Config.M365_LICENCE_SKUS.get(hire.get("employmentType", "Permanent"), "")
    if sku_id:
        try:
            _graph("POST", f"users/{object_id}/assignLicense", token, {
                "addLicenses": [{"skuId": sku_id, "disabledPlans": []}],
                "removeLicenses": []
            })
            result["licenseAssigned"] = True
            log.info("Assigned M365 license (%s) to %s", sku_id, upn)
        except requests.HTTPError as exc:
            result["errors"].append(f"License assignment failed: {exc}")
    else:
        result["errors"].append("No license SKU configured for this employment type.")

    # Step 3: Set manager
    manager_id = _find_manager_object_id(hire.get("managerEmail", ""), token)
    if manager_id:
        try:
            _graph("PUT", f"users/{object_id}/manager/$ref", token, {
                "@odata.id": f"{GRAPH_BASE}/users/{manager_id}"
            })
            result["managerSet"] = True
            log.info("Set manager %s for %s", hire.get("managerEmail"), upn)
        except requests.HTTPError as exc:
            result["errors"].append(f"Manager set failed: {exc}")

    # Step 4: Add to department security group
    group_id = _get_department_group_id(hire.get("department", ""), token)
    if group_id:
        try:
            _graph("POST", f"groups/{group_id}/members/$ref", token, {
                "@odata.id": f"{GRAPH_BASE}/directoryObjects/{object_id}"
            })
            result["groupAdded"] = True
            log.info("Added %s to %s security group", upn, hire.get("department"))
        except requests.HTTPError as exc:
            result["errors"].append(f"Group add failed: {exc}")

    result["success"] = result["licenseAssigned"] and not any(
        "failed" in e.lower() for e in result["errors"]
    )
    return result


def enable_account_on_day_one(object_id: str) -> bool:
    """Enable the AD account on the morning of the hire's start date."""
    try:
        token = _get_token()
        _graph("PATCH", f"users/{object_id}", token, {"accountEnabled": True})
        log.info("Enabled AD account for objectId: %s", object_id)
        return True
    except Exception as exc:
        log.error("Failed to enable AD account %s: %s", object_id, exc)
        return False
