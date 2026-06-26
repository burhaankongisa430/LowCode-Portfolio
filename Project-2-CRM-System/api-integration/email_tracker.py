"""
Microsoft Graph API email & calendar activity tracker.
Polls each sales rep's mailbox for emails and calendar events related to CRM contacts,
then writes matching interactions to the Quickbase Activities table.

Requires:
  - Azure AD App Registration with Mail.Read + Calendars.Read (application permissions)
  - GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET in .env
  - MSAL (Microsoft Authentication Library) — see requirements.txt

Run on a schedule (APScheduler, every 30 minutes) via webhook_handler.py.
"""

import logging
from datetime import datetime, timezone, timedelta

import msal
import requests

from config import Config
from quickbase_client import CRMQuickbaseClient

log = logging.getLogger(__name__)
qb = CRMQuickbaseClient()

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _get_access_token() -> str:
    """Acquire an app-only access token using client credentials flow."""
    app = msal.ConfidentialClientApplication(
        client_id=Config.GRAPH_CLIENT_ID,
        client_credential=Config.GRAPH_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{Config.GRAPH_TENANT_ID}",
    )
    result = app.acquire_token_for_client(scopes=Config.GRAPH_SCOPES)
    if "access_token" not in result:
        raise RuntimeError(f"Graph token error: {result.get('error_description', 'Unknown')}")
    return result["access_token"]


def _graph_get(path: str, token: str, params: dict = None) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.get(f"{GRAPH_BASE}/{path.lstrip('/')}", headers=headers,
                     params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _get_rep_emails(user_id: str, token: str, since: datetime) -> list[dict]:
    """Fetch emails sent or received by a rep since the given datetime."""
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "$filter": f"receivedDateTime ge {since_str}",
        "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview,conversationId",
        "$top": 50,
        "$orderby": "receivedDateTime desc",
    }
    try:
        data = _graph_get(f"users/{user_id}/messages", token, params)
        return data.get("value", [])
    except requests.HTTPError as exc:
        log.warning("Failed to fetch emails for %s: %s", user_id, exc)
        return []


def _get_rep_calendar_events(user_id: str, token: str, since: datetime) -> list[dict]:
    """Fetch calendar events (meetings/calls) for a rep in the last sync window."""
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "$filter": f"start/dateTime ge '{since_str}' and start/dateTime le '{now_str}'",
        "$select": "id,subject,start,end,attendees,bodyPreview,onlineMeeting",
        "$top": 50,
    }
    try:
        data = _graph_get(f"users/{user_id}/events", token, params)
        return data.get("value", [])
    except requests.HTTPError as exc:
        log.warning("Failed to fetch calendar for %s: %s", user_id, exc)
        return []


def _extract_external_emails(message: dict, rep_email: str) -> list[str]:
    """Get all email addresses in a message that are not the rep themselves."""
    addresses = set()
    sender = message.get("from", {}).get("emailAddress", {}).get("address", "").lower()
    if sender and sender != rep_email.lower():
        addresses.add(sender)
    for recipient in message.get("toRecipients", []):
        addr = recipient.get("emailAddress", {}).get("address", "").lower()
        if addr and addr != rep_email.lower():
            addresses.add(addr)
    return list(addresses)


def _extract_attendee_emails(event: dict, rep_email: str) -> list[str]:
    """Get all attendee emails from a calendar event excluding the rep."""
    addresses = set()
    for attendee in event.get("attendees", []):
        addr = attendee.get("emailAddress", {}).get("address", "").lower()
        if addr and addr != rep_email.lower():
            addresses.add(addr)
    return list(addresses)


def sync_rep_activities(rep_email: str, rep_name: str, token: str) -> dict:
    """
    Sync emails and calendar events for one rep.
    Matches each message/event against CRM contacts by email.
    Writes matched interactions to Quickbase Activities table.
    Returns a summary dict.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=35)
    summary = {"emails_checked": 0, "events_checked": 0, "activities_logged": 0}

    emails = _get_rep_emails(rep_email, token, since)
    summary["emails_checked"] = len(emails)

    for msg in emails:
        external = _extract_external_emails(msg, rep_email)
        for email_addr in external:
            contact = qb.find_contact_by_email(email_addr)
            if not contact:
                continue
            try:
                qb.log_activity(
                    deal_record_id=0,
                    contact_record_id=contact["recordId"],
                    activity_type="Email Sent" if msg.get("from", {}).get("emailAddress", {}).get("address", "").lower() == rep_email.lower() else "Email Received",
                    subject=msg.get("subject", "(No Subject)"),
                    notes=msg.get("bodyPreview", "")[:500],
                    outcome="Neutral",
                    logged_by=rep_name,
                    logged_by_email=rep_email,
                    source="Graph API",
                )
                summary["activities_logged"] += 1
                log.debug("Logged email activity: %s ↔ %s", rep_email, email_addr)
            except Exception as exc:
                log.error("Failed to log email activity: %s", exc)

    events = _get_rep_calendar_events(rep_email, token, since)
    summary["events_checked"] = len(events)

    for event in events:
        attendees = _extract_attendee_emails(event, rep_email)
        for email_addr in attendees:
            contact = qb.find_contact_by_email(email_addr)
            if not contact:
                continue
            duration = 0
            try:
                start = datetime.fromisoformat(event["start"]["dateTime"].rstrip("Z"))
                end = datetime.fromisoformat(event["end"]["dateTime"].rstrip("Z"))
                duration = int((end - start).total_seconds() / 60)
            except (KeyError, ValueError):
                pass
            try:
                qb.log_activity(
                    deal_record_id=0,
                    contact_record_id=contact["recordId"],
                    activity_type="Meeting",
                    subject=event.get("subject", "(No Subject)"),
                    notes=event.get("bodyPreview", "")[:500],
                    outcome="Neutral",
                    logged_by=rep_name,
                    logged_by_email=rep_email,
                    source="Graph API",
                )
                summary["activities_logged"] += 1
            except Exception as exc:
                log.error("Failed to log calendar activity: %s", exc)

    return summary


def run_activity_sync(reps: list[dict]) -> dict:
    """
    Main sync job — run for all active reps.
    Called on a 30-minute schedule by the APScheduler in webhook_handler.py.

    reps: list of {"email": str, "name": str}
    """
    log.info("Starting Graph API activity sync for %d reps", len(reps))
    token = _get_access_token()
    total = {"emails_checked": 0, "events_checked": 0, "activities_logged": 0}

    for rep in reps:
        try:
            result = sync_rep_activities(rep["email"], rep["name"], token)
            for key in total:
                total[key] += result.get(key, 0)
        except Exception as exc:
            log.error("Sync failed for %s: %s", rep["email"], exc)

    log.info(
        "Activity sync complete — Emails: %d | Events: %d | Logged: %d",
        total["emails_checked"], total["events_checked"], total["activities_logged"],
    )
    return total
