"""
SLA monitoring engine.
Runs on a schedule (every 15 minutes via APScheduler) and processes all open tickets.
Triggers Teams notifications and Power Automate escalation flows for At Risk and Breached tickets.
"""

import logging
import requests
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from quickbase_client import QuickbaseClient
from teams_notifier import TeamsNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

qb = QuickbaseClient()
teams = TeamsNotifier()


def compute_sla_status(ticket: dict) -> str:
    """Recompute SLA status in Python (mirrors the Quickbase formula)."""
    if ticket.get("resolutionDate"):
        due = ticket.get("dueDate")
        resolved = ticket.get("resolutionDate")
        if due and resolved:
            return "Met" if resolved <= due else "Breached"
        return "Met"

    time_remaining = ticket.get("timeRemainingHours")
    if time_remaining is None:
        return "Unknown"

    resolution_sla = Config.SLA_POLICIES.get(ticket.get("priority", ""), {}).get("resolution", 24)
    at_risk_threshold = resolution_sla * 0.15

    if time_remaining < 0:
        return "Breached"
    if time_remaining <= at_risk_threshold:
        return "At Risk"
    return "On Track"


def _trigger_escalation_flow(ticket: dict, hours_overdue: float) -> None:
    if not Config.PA_ESCALATION_FLOW_URL:
        return
    payload = {
        "recordId":       ticket["recordId"],
        "ticketId":       ticket["ticketId"],
        "title":          ticket.get("title", ""),
        "priority":       ticket.get("priority", ""),
        "status":         ticket.get("status", ""),
        "submitterName":  ticket.get("submitterName", ""),
        "submitterEmail": ticket.get("submitterEmail", ""),
        "agentEmail":     ticket.get("assignedAgent", ""),
        "team":           ticket.get("assignedTeam", ""),
        "dueDate":        str(ticket.get("dueDate", "")),
        "slaStatus":      "Breached",
        "hoursOverdue":   round(hours_overdue, 2),
    }
    try:
        requests.post(Config.PA_ESCALATION_FLOW_URL, json=payload, timeout=10)
    except requests.RequestException as exc:
        log.error("Failed to trigger escalation flow for %s: %s", ticket["ticketId"], exc)


def run_sla_check() -> dict:
    """
    Main SLA check job. Runs every 15 minutes.
    Returns a summary dict with counts for logging/reporting.
    """
    log.info("Starting SLA check — %s UTC", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))

    try:
        open_tickets = qb.get_open_tickets()
    except Exception as exc:
        log.error("Failed to fetch open tickets from Quickbase: %s", exc)
        return {"error": str(exc)}

    summary = {"total": len(open_tickets), "on_track": 0, "at_risk": 0, "breached": 0, "p1_breaches": 0}

    for ticket in open_tickets:
        status = compute_sla_status(ticket)
        ticket_id = ticket.get("ticketId", "UNKNOWN")
        priority = ticket.get("priority", "")

        if status == "On Track":
            summary["on_track"] += 1

        elif status == "At Risk":
            summary["at_risk"] += 1
            log.warning("At Risk: %s (%s) — %.1fh remaining",
                        ticket_id, priority, ticket.get("timeRemainingHours", 0))
            teams.post_at_risk_warning(ticket)

        elif status == "Breached":
            summary["breached"] += 1
            if priority == "P1-Critical":
                summary["p1_breaches"] += 1
            hours_overdue = abs(ticket.get("timeRemainingHours", 0))
            log.error("BREACH: %s (%s) — %.1fh overdue", ticket_id, priority, hours_overdue)
            teams.post_sla_breach(ticket)
            _trigger_escalation_flow(ticket, hours_overdue)

    log.info(
        "SLA check complete — Total: %d | On Track: %d | At Risk: %d | Breached: %d | P1 Breaches: %d",
        summary["total"], summary["on_track"], summary["at_risk"],
        summary["breached"], summary["p1_breaches"],
    )
    return summary


def start_scheduler() -> BackgroundScheduler:
    """Start the APScheduler background job for SLA monitoring."""
    scheduler = BackgroundScheduler(timezone="Africa/Johannesburg")
    scheduler.add_job(run_sla_check, "interval", minutes=15, id="sla_monitor",
                      next_run_time=datetime.now(timezone.utc))
    scheduler.start()
    log.info("SLA monitor scheduler started — running every 15 minutes")
    return scheduler
