"""
Extractor: EmployeeOnboarding Quickbase app.
Pulls all KPIs needed for the People domain score.
"""

import logging
import requests
from config import Config

log = logging.getLogger(__name__)

_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _query(table_id: str, select: list, where: str = "", top: int = 500) -> list:
    body = {"from": table_id, "select": select, "options": {"top": top}}
    if where:
        body["where"] = where
    r = requests.post("https://api.quickbase.com/v1/records/query",
                      headers=_HEADERS, json=body, timeout=15)
    r.raise_for_status()
    return r.json().get("data", [])


def extract() -> dict:
    """
    Returns normalized People / Onboarding KPIs.
    """
    log.info("Extracting Onboarding KPIs...")

    employees = _query(
        Config.QB_EMPLOYEES_TABLE,
        select=[3, 24, 25, 27, 29, 30, 31, 32, 33, 34, 38],
        top=500,
    )

    def v(emp, fid): return emp.get(str(fid), {}).get("value")

    active = [e for e in employees if v(e, 24) in ("Active", "Pre-boarding")]
    completed = [e for e in employees if v(e, 24) == "Completed"]

    on_track  = sum(1 for e in active if v(e, 38) == "On Track")
    at_risk   = sum(1 for e in active if v(e, 38) == "At Risk")
    delayed   = sum(1 for e in active if v(e, 38) == "Delayed")

    on_track_rate = (on_track / len(active) * 100) if active else 100.0

    completion_days = [float(v(e, 29) or 0) for e in completed if v(e, 29)]
    avg_completion  = sum(completion_days) / len(completion_days) if completion_days else 0

    day1_ready     = sum(1 for e in employees if v(e, 33) and v(e, 34))
    started        = sum(1 for e in employees if v(e, 24) in ("Active", "Completed"))
    day1_readiness = (day1_ready / started * 100) if started else 0

    overdue_tasks = _query(
        Config.QB_OB_TASKS_TABLE,
        select=[3, 20],
        where="{20.EX.'true'} AND {13.XEX.'Completed'} AND {13.XEX.'N/A'}",
    )

    log.info("Onboarding: %d active | %.1f%% on track | avg %.1f days to complete",
             len(active), on_track_rate, avg_completion)

    return {
        "active_onboarding":         len(active),
        "completed_total":           len(completed),
        "on_track_count":            on_track,
        "at_risk_count":             at_risk,
        "delayed_count":             delayed,
        "on_track_rate":             round(on_track_rate, 2),
        "avg_completion_days":       round(avg_completion, 1),
        "day1_readiness_rate":       round(day1_readiness, 2),
        "overdue_tasks_total":       len(overdue_tasks),
    }
