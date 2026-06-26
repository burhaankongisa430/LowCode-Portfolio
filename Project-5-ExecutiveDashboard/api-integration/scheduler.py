"""
ETL Orchestrator — runs the full pipeline on a schedule.

Responsibilities:
  1. Extract domain data from all 4 source QB apps (in parallel, isolated)
  2. Compute KPI scores and alerts
  3. Write snapshot to QB KPI Snapshots table
  4. Write snapshot to Dataverse (Power BI source)
  5. Trigger Power Automate flows (alerts, weekly report)
  6. Gracefully degrade if any single source is unavailable

Run standalone:
  python scheduler.py

Or import run_etl() for the Flask webhook endpoint.
"""

import logging
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from config import Config
from kpi_calculator import compute
from dataverse_loader import write_snapshot
from report_generator import build_html, get_subject

log = logging.getLogger(__name__)

_QB_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _write_snapshot_to_qb(kpis: dict) -> bool:
    """Write the KPI snapshot record to the QB Snapshots table."""
    try:
        data = {
            "7":  {"value": kpis["snapshot_time"]},
            "11": {"value": kpis["health_score"]},
            "14": {"value": kpis["operational_score"]},
            "15": {"value": kpis["commercial_score"]},
            "16": {"value": kpis["people_score"]},
            "17": {"value": kpis["finance_score"]},
            "18": {"value": kpis["sla_met_rate"]},
            "19": {"value": kpis["active_breaches"]},
            "20": {"value": kpis["avg_resolution_hours"]},
            "21": {"value": kpis["open_tickets"]},
            "22": {"value": kpis["weighted_pipeline"]},
            "23": {"value": kpis["won_revenue_mtd"]},
            "24": {"value": kpis["win_rate"]},
            "25": {"value": kpis["quota_attainment"]},
            "26": {"value": kpis["stalled_deals"]},
            "27": {"value": kpis["active_onboarding"]},
            "28": {"value": kpis["onboarding_on_track_rate"]},
            "29": {"value": kpis["avg_completion_days"]},
            "30": {"value": kpis["day1_readiness_rate"]},
            "31": {"value": kpis["committed_spend_mtd"]},
            "32": {"value": kpis["avg_budget_util"]},
            "33": {"value": kpis["pending_approvals"]},
            "34": {"value": kpis["approval_cycle_days"]},
            "35": {"value": kpis["domains_available"]},
            "36": {"value": str(kpis.get("etl_errors", []))},
            "10": {"value": kpis["etl_duration_seconds"]},
        }
        r = requests.post(
            "https://api.quickbase.com/v1/records",
            headers=_QB_HEADERS,
            json={"to": Config.QB_SNAPSHOTS_TABLE, "data": [data]},
            timeout=15,
        )
        r.raise_for_status()
        log.info("QB snapshot written (health=%.1f)", kpis["health_score"])
        return True
    except Exception as exc:
        log.error("QB snapshot write failed: %s", exc)
        return False


def _trigger_pa_flow(url: str, payload: dict) -> bool:
    if not url:
        return False
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok
    except Exception as exc:
        log.warning("PA flow trigger failed: %s", exc)
        return False


def run_etl(is_weekly_report: bool = False) -> dict:
    """
    Full ETL pipeline run. Returns the complete KPI payload.
    is_weekly_report=True triggers the executive HTML email.
    """
    start = time.monotonic()
    now = datetime.now(timezone.utc)
    snapshot_time = now.isoformat()

    log.info("ETL pipeline starting — %s", now.strftime("%Y-%m-%d %H:%M UTC"))

    # Import extractors here to keep the module importable even if one is broken
    from extractors import service_desk_extractor, crm_extractor, onboarding_extractor, procurement_extractor

    domain_extractors = {
        "operational": service_desk_extractor.extract,
        "commercial":  crm_extractor.extract,
        "people":      onboarding_extractor.extract,
        "finance":     procurement_extractor.extract,
    }

    domain_data = {}
    etl_errors = []

    # Run all 4 extractors in parallel — isolate failures per domain
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn): name for name, fn in domain_extractors.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                domain_data[name] = future.result()
            except Exception as exc:
                log.error("Extractor '%s' failed: %s", name, exc)
                domain_data[name] = None
                etl_errors.append(f"{name}: {str(exc)[:100]}")

    domains_available = sum(1 for v in domain_data.values() if v is not None)
    etl_duration = round(time.monotonic() - start, 2)

    kpis = compute(
        ops=domain_data.get("operational"),
        crm=domain_data.get("commercial"),
        hr=domain_data.get("people"),
        fin=domain_data.get("finance"),
        domains_available=domains_available,
        etl_duration=etl_duration,
    )
    kpis["snapshot_time"] = snapshot_time
    kpis["etl_errors"] = etl_errors

    # Write to QB and Dataverse in parallel
    with ThreadPoolExecutor(max_workers=2) as pool:
        qb_future = pool.submit(_write_snapshot_to_qb, kpis)
        dv_future = pool.submit(write_snapshot, kpis)
        kpis["qb_written"]        = qb_future.result()
        kpis["dataverse_written"] = dv_future.result()

    # Trigger PA Dataverse sync flow (belt-and-suspenders if direct write fails)
    if not kpis["dataverse_written"] and Config.PA_DATAVERSE_SYNC_URL:
        _trigger_pa_flow(Config.PA_DATAVERSE_SYNC_URL, kpis)

    # Trigger PA alert flow if any thresholds breached
    if kpis.get("alerts") and Config.PA_ALERT_FLOW_URL:
        _trigger_pa_flow(Config.PA_ALERT_FLOW_URL, kpis)

    # Generate and send weekly report if Monday or forced
    if is_weekly_report and Config.PA_REPORT_FLOW_URL:
        html = build_html(kpis)
        subject = get_subject(kpis)
        _trigger_pa_flow(Config.PA_REPORT_FLOW_URL, {
            "reportHtml":       html,
            "reportDate":       now.strftime("%Y-%m-%d"),
            "reportSubject":    subject,
            "healthScore":      kpis["health_score"],
            "healthStatus":     kpis["health_status"],
            "operationalScore": kpis["operational_score"],
            "commercialScore":  kpis["commercial_score"],
            "peopleScore":      kpis["people_score"],
            "financeScore":     kpis["finance_score"],
            "topAlert":         kpis["alerts"][0]["message"] if kpis["alerts"] else "",
        })
        kpis["report_sent"] = True

    kpis["etl_duration_seconds"] = round(time.monotonic() - start, 2)
    log.info("ETL complete in %.2fs | health=%.1f | alerts=%d",
             kpis["etl_duration_seconds"], kpis["health_score"], len(kpis.get("alerts", [])))
    return kpis


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from apscheduler.schedulers.blocking import BlockingScheduler
    from datetime import datetime as dt

    scheduler = BlockingScheduler(timezone="Africa/Johannesburg")

    # Every 15 minutes
    scheduler.add_job(run_etl, "interval", minutes=15, id="etl_15min",
                      kwargs={"is_weekly_report": False})

    # Monday 06:30 — full ETL + report
    scheduler.add_job(run_etl, "cron", day_of_week="mon", hour=6, minute=30,
                      id="weekly_report",
                      kwargs={"is_weekly_report": True})

    log.info("Scheduler started — ETL every 15 min, report Mondays 06:30 SAST")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")
