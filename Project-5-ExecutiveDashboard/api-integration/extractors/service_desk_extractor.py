"""
Extractor: ServiceDeskAutomation Quickbase app.
Pulls all KPIs needed for the Operational domain score.
"""

import logging
import requests
from datetime import datetime, timezone, timedelta
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
    Returns a normalized dict of Service Desk KPIs.
    Keys match the unified schema expected by kpi_calculator.py.
    On failure raises an exception — caller handles graceful degradation.
    """
    log.info("Extracting Service Desk KPIs...")

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_tickets = _query(
        Config.QB_TICKETS_TABLE,
        select=[3, 10, 11, 16, 21, 22],
        where="{11.XEX.'Draft'}",
        top=5000,
    )

    total_open = sum(1 for t in all_tickets
                     if t.get("11", {}).get("value") not in ("Resolved", "Closed"))
    resolved = [t for t in all_tickets
                if t.get("11", {}).get("value") in ("Resolved", "Closed")]

    sla_met    = sum(1 for t in resolved if t.get("22", {}).get("value") == "Met")
    sla_breached_open = sum(1 for t in all_tickets
                            if t.get("22", {}).get("value") == "Breached"
                            and t.get("11", {}).get("value") not in ("Resolved", "Closed"))
    p1_breached = sum(1 for t in all_tickets
                      if t.get("10", {}).get("value") == "P1-Critical"
                      and t.get("22", {}).get("value") == "Breached"
                      and t.get("11", {}).get("value") not in ("Resolved", "Closed"))

    res_times = [float(t["21"]["value"]) for t in resolved
                 if t.get("21", {}).get("value") is not None]
    avg_resolution_hours = sum(res_times) / len(res_times) if res_times else 0

    sla_met_rate = (sla_met / len(resolved) * 100) if resolved else 100.0

    tickets_this_week = sum(1 for t in all_tickets
                            if (t.get("16", {}).get("value") or "") >= week_ago)
    two_weeks_ago = (now - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    tickets_last_week = sum(1 for t in all_tickets
                            if two_weeks_ago <= (t.get("16", {}).get("value") or "") < week_ago)

    log.info("Service Desk: %d open | SLA met %.1f%% | %d breaches",
             total_open, sla_met_rate, sla_breached_open)

    return {
        "open_tickets":           total_open,
        "sla_met_rate":           round(sla_met_rate, 2),
        "active_breaches":        sla_breached_open,
        "avg_resolution_hours":   round(avg_resolution_hours, 2),
        "p1_breach_count":        p1_breached,
        "tickets_this_week":      tickets_this_week,
        "tickets_last_week":      tickets_last_week,
        "tickets_wow_change_pct": round(
            (tickets_this_week - tickets_last_week) / max(1, tickets_last_week) * 100, 1
        ),
        "total_resolved":         len(resolved),
    }
