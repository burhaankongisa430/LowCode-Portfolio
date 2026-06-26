"""
Flask webhook intake server.
Receives ticket submissions from external systems (email parsers, Jira, Zendesk, etc.)
and creates Quickbase records via the QB REST API.

Run with:
    python webhook_handler.py                    # dev (Flask dev server)
    waitress-serve --port=5000 webhook_handler:app  # production
"""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify

from config import Config
from quickbase_client import QuickbaseClient, QuickbaseError
from teams_notifier import TeamsNotifier
from sla_monitor import start_scheduler

log = logging.getLogger(__name__)
app = Flask(__name__)

qb = QuickbaseClient()
teams = TeamsNotifier()


# ------------------------------------------------------------------ #
#  Auth middleware                                                     #
# ------------------------------------------------------------------ #

def _verify_signature(req) -> bool:
    """Validate the HMAC-SHA256 webhook signature from trusted callers."""
    sig_header = req.headers.get("X-Webhook-Signature", "")
    if not sig_header:
        return False
    expected = hmac.new(
        Config.WEBHOOK_SECRET.encode(),
        req.get_data(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", sig_header)


# ------------------------------------------------------------------ #
#  Input validation                                                    #
# ------------------------------------------------------------------ #

def _validate_ticket_payload(data: dict) -> list[str]:
    errors = []
    required = ["title", "description", "category", "priority", "submitterName", "submitterEmail"]
    for field in required:
        if not data.get(field, "").strip():
            errors.append(f"'{field}' is required and cannot be blank.")

    if data.get("priority") and data["priority"] not in Config.VALID_PRIORITIES:
        errors.append(f"Invalid priority '{data['priority']}'. Must be one of: {Config.VALID_PRIORITIES}")

    if data.get("category") and data["category"] not in Config.VALID_CATEGORIES:
        errors.append(f"Invalid category '{data['category']}'. Must be one of: {Config.VALID_CATEGORIES}")

    if data.get("submitterEmail") and "@" not in data["submitterEmail"]:
        errors.append("'submitterEmail' must be a valid email address.")

    return errors


# ------------------------------------------------------------------ #
#  Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/tickets", methods=["POST"])
def create_ticket():
    """
    Create a new service desk ticket from an external system.

    Expected JSON body:
    {
        "title":          "Laptop won't connect to VPN",
        "description":    "Full description of the issue...",
        "category":       "IT-Network",
        "priority":       "P2-High",
        "submitterName":  "Jane Smith",
        "submitterEmail": "jane.smith@company.com",
        "tags":           "vpn,remote-work"  (optional)
    }
    """
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized — invalid or missing webhook signature."}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    errors = _validate_ticket_payload(data)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 422

    try:
        result = qb.create_ticket(
            title=data["title"].strip(),
            description=data["description"].strip(),
            category=data["category"],
            priority=data["priority"],
            submitter_name=data["submitterName"].strip(),
            submitter_email=data["submitterEmail"].strip().lower(),
            tags=data.get("tags", ""),
        )
    except QuickbaseError as exc:
        log.error("QB create_ticket failed: %s", exc)
        return jsonify({"error": "Failed to create ticket in Quickbase.", "detail": str(exc)}), 502

    qb.log_audit_event(
        ticket_record_id=result["recordId"],
        action="Created via API",
        new_value=f"Submitted by {data['submitterEmail']} via webhook",
    )

    teams.post_new_ticket({**result, **data})

    log.info("Ticket created: %s (%s)", result["ticketId"], data["priority"])

    return jsonify({
        "ticketId":  result["ticketId"],
        "recordId":  result["recordId"],
        "dueDate":   result["dueDate"],
        "message":   "Ticket created successfully. Confirmation sent to submitter.",
    }), 201


@app.route("/api/tickets/<int:record_id>", methods=["GET"])
def get_ticket(record_id: int):
    """Fetch a single ticket by Quickbase record ID."""
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    ticket = qb.get_ticket(record_id)
    if not ticket:
        return jsonify({"error": f"Ticket with recordId {record_id} not found."}), 404

    return jsonify(ticket), 200


@app.route("/api/tickets/<int:record_id>/status", methods=["PATCH"])
def update_ticket_status(record_id: int):
    """
    Update a ticket's status.

    JSON body: { "status": "In Progress", "notes": "Working on it now." }
    """
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()

    if new_status not in Config.VALID_STATUSES:
        return jsonify({
            "error": f"Invalid status '{new_status}'.",
            "valid": Config.VALID_STATUSES
        }), 422

    fields = {11: new_status}
    if new_status == "Resolved":
        fields[20] = datetime.now(timezone.utc).isoformat()
    if data.get("notes"):
        fields[33] = data["notes"]

    try:
        qb.update_ticket(record_id, fields)
    except QuickbaseError as exc:
        log.error("QB update_ticket failed: %s", exc)
        return jsonify({"error": "Failed to update ticket.", "detail": str(exc)}), 502

    qb.log_audit_event(
        ticket_record_id=record_id,
        action="Status Change via API",
        new_value=new_status,
        performed_by=request.headers.get("X-Agent-Name", "API"),
        performed_by_email=request.headers.get("X-Agent-Email", "api@system"),
    )

    return jsonify({"recordId": record_id, "newStatus": new_status, "updated": True}), 200


@app.route("/api/sla/check", methods=["POST"])
def trigger_sla_check():
    """Manually trigger an SLA check (for testing or on-demand runs)."""
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    from sla_monitor import run_sla_check
    summary = run_sla_check()
    return jsonify({"result": "SLA check complete", "summary": summary}), 200


# ------------------------------------------------------------------ #
#  Error handlers                                                     #
# ------------------------------------------------------------------ #

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed."}), 405


@app.errorhandler(500)
def internal_error(e):
    log.exception("Unhandled exception")
    return jsonify({"error": "An internal server error occurred."}), 500


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        app.run(
            host="0.0.0.0",
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=False,
        )
    finally:
        scheduler.shutdown()
