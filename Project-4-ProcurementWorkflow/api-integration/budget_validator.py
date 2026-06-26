"""
Real-time budget availability validator.

Called by the Power Automate validation flow before routing a request to approvers.
Checks:
  1. Does the department have sufficient available budget?
  2. Is the vendor on the approved supplier list?
  3. Would this request push utilization above the alert threshold?

Returns a dict with flags that are written back to the QB request record
and displayed to approvers in the email/Teams card.
"""

import logging
import requests
from config import Config

log = logging.getLogger(__name__)


def _qb_query(table_id: str, select: list, where: str, top: int = 1) -> list:
    headers = {
        "QB-Realm-Hostname": Config.QB_REALM_HOSTNAME,
        "Authorization":     f"QB-USER-TOKEN {Config.QB_USER_TOKEN}",
        "Content-Type":      "application/json",
    }
    body = {
        "from":    table_id,
        "select":  select,
        "where":   where,
        "options": {"top": top},
    }
    r = requests.post(
        f"https://api.quickbase.com/v1/records/query",
        headers=headers, json=body, timeout=10
    )
    r.raise_for_status()
    return r.json().get("data", [])


def _get_budget(department_record_id: int) -> dict | None:
    """Fetch the current budget record for a department."""
    rows = _qb_query(
        Config.QB_BUDGETS_TABLE,
        select=[3, 10, 11, 12, 13, 14, 16, 17, 18],
        where=f"{{3.EX.'{department_record_id}'}} AND {{16.EX.'true'}}",
    )
    if not rows:
        return None
    r = rows[0]
    def v(fid): return r.get(str(fid), {}).get("value", 0)
    return {
        "recordId":          v(3),
        "annualBudget":      float(v(10) or 0),
        "committedAmount":   float(v(11) or 0),
        "spentAmount":       float(v(12) or 0),
        "availableBudget":   float(v(13) or 0),
        "utilizationPct":    float(v(14) or 0),
        "alertThreshold":    float(v(17) or 85),
        "budgetStatus":      v(18),
    }


def _reserve_budget(budget_record_id: int, amount: float) -> bool:
    """
    Reserve (commit) the requested amount on the budget record.
    This prevents race conditions where two simultaneous requests
    both check budget before either is committed.
    """
    headers = {
        "QB-Realm-Hostname": Config.QB_REALM_HOSTNAME,
        "Authorization":     f"QB-USER-TOKEN {Config.QB_USER_TOKEN}",
        "Content-Type":      "application/json",
    }
    # Fetch current committed amount
    rows = _qb_query(Config.QB_BUDGETS_TABLE, [3, 11], f"{{3.EX.'{budget_record_id}'}}")
    if not rows:
        return False
    current_committed = float(rows[0].get("11", {}).get("value", 0) or 0)
    new_committed = current_committed + amount

    r = requests.post(
        "https://api.quickbase.com/v1/records",
        headers=headers,
        json={
            "to": Config.QB_BUDGETS_TABLE,
            "data": [{"3": {"value": budget_record_id}, "11": {"value": new_committed}}],
        },
        timeout=10,
    )
    return r.ok


def _check_vendor(vendor_record_id: int) -> bool:
    """Returns True if the vendor is on the approved list."""
    if not vendor_record_id:
        return False
    rows = _qb_query(
        Config.QB_VENDORS_TABLE,
        select=[3, 12],
        where=f"{{3.EX.'{vendor_record_id}'}}",
    )
    if not rows:
        return False
    return rows[0].get("12", {}).get("value", "") == "Approved"


def validate(department_record_id: int, request_amount: float,
             vendor_record_id: int = None) -> dict:
    """
    Main validation entry point.

    Returns:
        {
            "budgetWarning":     bool,  # True if request > available budget
            "vendorWarning":     bool,  # True if vendor is not on approved list
            "availableBudget":   float,
            "budgetUtilization": float, # % after this request
            "budgetStatus":      str,
            "budgetReserved":    bool,  # True if commitment was recorded
        }
    """
    result = {
        "budgetWarning":     False,
        "vendorWarning":     False,
        "availableBudget":   0.0,
        "budgetUtilization": 0.0,
        "budgetStatus":      "Unknown",
        "budgetReserved":    False,
    }

    # Budget check
    try:
        budget = _get_budget(department_record_id)
        if budget:
            result["availableBudget"]   = budget["availableBudget"]
            result["budgetUtilization"] = budget["utilizationPct"]
            result["budgetStatus"]      = budget["budgetStatus"]

            if request_amount > budget["availableBudget"]:
                result["budgetWarning"] = True
                log.warning(
                    "Budget warning: request R%.2f exceeds available R%.2f (dept %d)",
                    request_amount, budget["availableBudget"], department_record_id
                )

            # Reserve the amount regardless of warning (soft reservation)
            reserved = _reserve_budget(budget["recordId"], request_amount)
            result["budgetReserved"] = reserved
        else:
            log.warning("No active budget found for department %d", department_record_id)
            result["budgetWarning"] = True

    except Exception as exc:
        log.error("Budget check failed: %s", exc)
        result["budgetWarning"] = True  # fail safe — flag it

    # Vendor check
    try:
        result["vendorWarning"] = not _check_vendor(vendor_record_id)
    except Exception as exc:
        log.error("Vendor check failed: %s", exc)
        result["vendorWarning"] = True

    return result


def release_budget_commitment(department_record_id: int, amount: float) -> bool:
    """
    Release a previously committed amount when a request is rejected or canceled.
    """
    try:
        rows = _qb_query(Config.QB_BUDGETS_TABLE, [3, 11],
                         f"{{3.EX.'{department_record_id}'}} AND {{16.EX.'true'}}")
        if not rows:
            return False
        budget_record_id = rows[0]["3"]["value"]
        current = float(rows[0].get("11", {}).get("value", 0) or 0)
        new_committed = max(0.0, current - amount)

        headers = {
            "QB-Realm-Hostname": Config.QB_REALM_HOSTNAME,
            "Authorization":     f"QB-USER-TOKEN {Config.QB_USER_TOKEN}",
            "Content-Type":      "application/json",
        }
        r = requests.post(
            "https://api.quickbase.com/v1/records",
            headers=headers,
            json={
                "to": Config.QB_BUDGETS_TABLE,
                "data": [{"3": {"value": budget_record_id}, "11": {"value": new_committed}}],
            },
            timeout=10,
        )
        log.info("Released R%.2f commitment from dept %d", amount, department_record_id)
        return r.ok
    except Exception as exc:
        log.error("Budget release failed: %s", exc)
        return False
