"""
BambooHR API connector — reads employee data from BambooHR.
Used when the hub needs to enrich an inbound BambooHR event with
additional employee fields not included in the webhook payload.
"""

import logging
import requests
from base64 import b64encode
from config import Config

log = logging.getLogger(__name__)

_BASE = f"https://api.bamboohr.com/api/gateway.php/{Config.BAMBOOHR_SUBDOMAIN}/v1"


def _auth_header() -> dict:
    creds = b64encode(f"{Config.BAMBOOHR_API_KEY}:x".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Accept": "application/json"}


def get_employee(employee_id: str) -> dict:
    """Fetch full employee record from BambooHR by employee ID."""
    fields = "firstName,lastName,workEmail,personalEmail,jobTitle,department,location,employmentHistoryStatus,hireDate,terminationDate,supervisorId,supervisor"
    r = requests.get(
        f"{_BASE}/employees/{employee_id}",
        headers=_auth_header(),
        params={"fields": fields},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def send(payload: dict) -> dict:
    """
    Send data back to BambooHR.
    Supported actions: update_employee_field
    """
    action = payload.get("action", "")
    if action == "update_employee_field":
        employee_id = payload["employee_id"]
        fields      = payload["fields"]
        r = requests.post(
            f"{_BASE}/employees/{employee_id}",
            headers={**_auth_header(), "Content-Type": "application/json"},
            json=fields,
            timeout=10,
        )
        r.raise_for_status()
        log.info("BambooHR update_employee_field — employee %s", employee_id)
        return {"status": "success", "employeeId": employee_id}

    raise ValueError(f"BambooHR connector: unsupported action '{action}'")
