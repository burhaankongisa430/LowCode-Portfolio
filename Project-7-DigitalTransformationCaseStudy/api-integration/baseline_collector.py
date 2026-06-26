"""
Baseline Collector — captures and stores before-state metrics in Quickbase.

Used during the discovery phase to record the AS-IS measurements that
become the denominator for all ROI and improvement calculations.

Also supports logging after-state measurements so the system can
automatically compute improvement percentages.
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


def _write(table: str, data: dict) -> dict:
    r = requests.post("https://api.quickbase.com/v1/records",
                      headers=_HEADERS,
                      json={"to": table, "data": [data], "fieldsToReturn": [3, 6]},
                      timeout=10)
    r.raise_for_status()
    return r.json()


def record_baseline_metric(
    initiative_record_id: int,
    metric_name: str,
    domain: str,
    before_value: float,
    unit: str,
    direction: str,           # "Higher is Better" | "Lower is Better"
    target_value: float,
    min_acceptable_improvement_pct: float,
    measurement_method: str,
    source: str,
    notes: str = "",
) -> dict:
    """
    Record a before-state baseline metric in the QB Process Baselines table.
    Called during the discovery phase before any platform is built.
    """
    log.info("Recording baseline: %s = %s %s", metric_name, before_value, unit)
    return _write(Config.QB_BASELINES_TABLE, {
        "6":  {"value": initiative_record_id},
        "7":  {"value": metric_name},
        "8":  {"value": domain},
        "9":  {"value": before_value},
        "10": {"value": unit},
        "11": {"value": direction},
        "13": {"value": target_value},
        "15": {"value": min_acceptable_improvement_pct},
        "17": {"value": measurement_method},
        "18": {"value": source},
        "19": {"value": notes},
        "20": {"value": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
    })


def record_after_metric(
    baseline_record_id: int,
    after_value: float,
    measured_by: str,
    measurement_notes: str = "",
) -> dict:
    """
    Update an existing baseline record with the after-state measurement.
    The Quickbase formula fields then auto-compute improvement % and target met.
    """
    log.info("Recording after-state for baseline record %d: %s", baseline_record_id, after_value)
    r = requests.post("https://api.quickbase.com/v1/records",
                      headers=_HEADERS,
                      json={"to": Config.QB_BASELINES_TABLE, "data": [{
                          "3":  {"value": baseline_record_id},
                          "12": {"value": after_value},
                          "21": {"value": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
                          "22": {"value": measured_by},
                          "23": {"value": measurement_notes},
                      }]},
                      timeout=10)
    r.raise_for_status()
    return r.json()


def get_all_baselines(initiative_record_id: int = None) -> list[dict]:
    """Fetch all baseline metrics, optionally filtered by initiative."""
    where = f"{{6.EX.'{initiative_record_id}'}}" if initiative_record_id else ""
    r = requests.post("https://api.quickbase.com/v1/records/query",
                      headers=_HEADERS,
                      json={
                          "from": Config.QB_BASELINES_TABLE,
                          "select": list(range(3, 28)),
                          "where": where,
                          "options": {"top": 500},
                      },
                      timeout=10)
    r.raise_for_status()
    return [_map_baseline(row) for row in r.json().get("data", [])]


def _map_baseline(row: dict) -> dict:
    def v(fid): return row.get(str(fid), {}).get("value")
    return {
        "recordId":          v(3),  "metricName":     v(7),
        "domain":            v(8),  "beforeValue":    v(9),
        "unit":              v(10), "direction":      v(11),
        "afterValue":        v(12), "targetValue":    v(13),
        "improvementPct":    v(14), "targetMet":      v(15),
        "measurementMethod": v(17), "source":         v(18),
        "notes":             v(19), "baselineDate":   v(20),
        "afterDate":         v(21), "measuredBy":     v(22),
    }


# ------------------------------------------------------------------ #
#  Seed function — load all Meridian baselines at project start       #
# ------------------------------------------------------------------ #

MERIDIAN_BASELINES = [
    # Service Desk (INIT-01)
    ("Service Desk", "SLA Met Rate",               "Operational", 66.0,  "%",    "Higher is Better", 90.0,  +20.0, "Manual weekly report",       "Historical records"),
    ("Service Desk", "Avg Resolution Time",        "Operational", 48.0,  "hours","Lower is Better",  24.0,  -40.0, "Email timestamp analysis",    "3 months email review"),
    ("Service Desk", "Admin & Routing Hours/Week", "Operational", 42.0,  "hours","Lower is Better",  10.0,  -50.0, "Time-in-motion study",        "2-day shadow, 3 agents"),
    ("Service Desk", "P1 Breaches per Month",      "Operational", 10.0,  "count","Lower is Better",  2.0,   -70.0, "Incident log",                "6-month average"),
    # CRM / Sales (INIT-02)
    ("CRM",          "Win Rate",                   "Commercial",  22.0,  "%",    "Higher is Better", 30.0,  +6.0,  "Deal spreadsheet",            "12-month history"),
    ("CRM",          "Avg Sales Cycle",            "Commercial",  8.3,   "days", "Lower is Better",  5.0,   -25.0, "Email thread timestamps",     "Sample 50 deals"),
    ("CRM",          "CRM Update Hours/Week",      "Commercial",  56.0,  "hours","Lower is Better",  4.0,   -80.0, "Rep survey",                  "8 reps × 7h estimate"),
    ("CRM",          "Forecast Accuracy",          "Commercial",  60.0,  "%",    "Higher is Better", 85.0,  +15.0, "Finance vs actuals (12 months)","CFO records"),
    # HR / Onboarding (INIT-03)
    ("Onboarding",   "Time-to-Productivity",       "People",      47.0,  "days", "Lower is Better",  30.0,  -30.0, "Manager survey",              "24 managers, 48 hires"),
    ("Onboarding",   "Onboarding Completion Rate", "People",      58.0,  "%",    "Higher is Better", 90.0,  +25.0, "HR tracking sheet",           "Annual records"),
    ("Onboarding",   "Day 1 System Access Rate",   "People",      31.0,  "%",    "Higher is Better", 90.0,  +40.0, "IT records",                  "6-month review"),
    ("Onboarding",   "HR Admin Hours per Hire",    "People",      18.0,  "hours","Lower is Better",  4.0,   -70.0, "Time study",                  "3 HR staff observed"),
    # Procurement (INIT-04)
    ("Procurement",  "Approval Cycle Time",        "Finance",     8.3,   "days", "Lower is Better",  2.0,   -60.0, "Email thread analysis",       "50 historical requests"),
    ("Procurement",  "PO Creation Time",           "Finance",     3.0,   "hours","Lower is Better",  0.0,   -100.0,"Finance team survey",         "80 POs/year"),
    ("Procurement",  "Budget Overspend Incidents", "Finance",     6.0,   "count","Lower is Better",  0.0,   -80.0, "Finance records",             "Annual"),
    # Integration (INIT-06)
    ("Integration",  "Cross-System Update Hours",  "Integration", 22.0,  "hours","Lower is Better",  2.0,   -80.0, "Cross-team survey",           "All departments"),
]


def seed_meridian_baselines(initiative_name_to_record_id: dict) -> None:
    """
    Seed all Meridian baseline metrics into Quickbase.
    initiative_name_to_record_id maps e.g. "Service Desk" → 123
    """
    for (init_name, metric, domain, before, unit, direction,
         target, min_pct, method, source) in MERIDIAN_BASELINES:
        rid = initiative_name_to_record_id.get(init_name)
        if not rid:
            log.warning("No record ID for initiative '%s' — skipping", init_name)
            continue
        try:
            record_baseline_metric(
                initiative_record_id=rid,
                metric_name=metric,
                domain=domain,
                before_value=before,
                unit=unit,
                direction=direction,
                target_value=target,
                min_acceptable_improvement_pct=min_pct,
                measurement_method=method,
                source=source,
            )
            log.info("Seeded: %s — %s", init_name, metric)
        except Exception as exc:
            log.error("Seed failed for %s/%s: %s", init_name, metric, exc)
