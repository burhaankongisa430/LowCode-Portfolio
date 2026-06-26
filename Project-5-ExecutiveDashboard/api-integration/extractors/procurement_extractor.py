"""
Extractor: ProcurementWorkflow Quickbase app.
Pulls all KPIs needed for the Finance domain score.
"""

import logging
import requests
from datetime import datetime, timezone
from config import Config

log = logging.getLogger(__name__)

_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _query(table_id: str, select: list, where: str = "", top: int = 1000) -> list:
    body = {"from": table_id, "select": select, "options": {"top": top}}
    if where:
        body["where"] = where
    r = requests.post("https://api.quickbase.com/v1/records/query",
                      headers=_HEADERS, json=body, timeout=15)
    r.raise_for_status()
    return r.json().get("data", [])


def extract() -> dict:
    """
    Returns normalized Finance / Procurement KPIs.
    """
    log.info("Extracting Procurement KPIs...")

    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")

    requests_data = _query(
        Config.QB_REQUESTS_TABLE,
        select=[3, 16, 19, 35, 39, 43],
        top=2000,
    )

    def v(r, fid): return r.get(str(fid), {}).get("value")

    pending = [r for r in requests_data if "Pending" in (v(r, 19) or "")]
    rejected = [r for r in requests_data if v(r, 19) == "Rejected"]
    approved = [r for r in requests_data if v(r, 19) in ("Approved", "PO Issued")]
    closed   = approved + rejected

    committed_mtd = sum(
        float(v(r, 16) or 0) for r in requests_data
        if v(r, 19) not in ("Rejected", "Canceled", "Draft")
        and (v(r, 39) or "")[:7] == current_month
    )

    sla_breaches = sum(1 for r in requests_data if v(r, 43) is True)
    unapproved_vendor = sum(1 for r in requests_data
                            if v(r, 35) is False
                            and v(r, 19) not in ("Rejected", "Canceled", "Draft"))

    rejection_rate = (len(rejected) / len(closed) * 100) if closed else 0

    # Approval cycle from history table
    hist = _query(
        Config.QB_APPROVAL_HIST_TABLE,
        select=[3, 13],
        where="{10.EX.'Approved'} AND {13.GT.'0'}",
    )
    cycle_hours = [float(h.get("13", {}).get("value") or 0) for h in hist if h.get("13", {}).get("value")]
    avg_cycle_hours = sum(cycle_hours) / len(cycle_hours) if cycle_hours else 0
    avg_cycle_days  = avg_cycle_hours / 24

    # Budget utilization
    budgets = _query(
        Config.QB_BUDGETS_TABLE,
        select=[3, 14],
        where="{16.EX.'true'}",
    )
    util_rates = [float(b.get("14", {}).get("value") or 0) for b in budgets]
    avg_util = sum(util_rates) / len(util_rates) if util_rates else 0
    over_budget_depts = sum(1 for u in util_rates if u >= 100)

    log.info("Procurement: %d pending | avg cycle %.1f days | avg util %.1f%%",
             len(pending), avg_cycle_days, avg_util)

    return {
        "committed_spend_mtd":    round(committed_mtd, 2),
        "pending_approvals":      len(pending),
        "avg_approval_cycle_days":round(avg_cycle_days, 2),
        "sla_breach_count":       sla_breaches,
        "rejection_rate":         round(rejection_rate, 2),
        "avg_budget_utilization": round(avg_util, 2),
        "over_budget_depts":      over_budget_depts,
        "unapproved_vendor_reqs": unapproved_vendor,
        "total_approved_count":   len(approved),
        "total_rejected_count":   len(rejected),
    }
