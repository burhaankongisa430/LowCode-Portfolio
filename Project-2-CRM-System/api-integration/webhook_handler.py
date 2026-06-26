"""
Flask webhook server for CRM & Sales Pipeline.
Handles external lead intake, lead scoring, and activity sync scheduling.

Endpoints:
  POST /api/leads          — intake from website form / marketing tools
  POST /api/score          — score a lead without creating a record
  POST /api/activities     — log an activity from external system
  PATCH /api/deals/<id>    — update deal stage from external system
  POST /api/sync/activities — manually trigger Graph API activity sync
  GET  /health             — health check

Run:
  python webhook_handler.py              (dev)
  waitress-serve --port=5001 webhook_handler:app  (prod)
"""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from quickbase_client import CRMQuickbaseClient, QuickbaseError
from lead_scorer import score_lead

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
qb = CRMQuickbaseClient()


# ------------------------------------------------------------------ #
#  Auth                                                               #
# ------------------------------------------------------------------ #

def _verify_signature(req) -> bool:
    sig = req.headers.get("X-Webhook-Signature", "")
    if not sig:
        return False
    expected = hmac.new(
        Config.WEBHOOK_SECRET.encode(), req.get_data(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", sig)


# ------------------------------------------------------------------ #
#  Validation                                                         #
# ------------------------------------------------------------------ #

def _validate_lead(data: dict) -> list[str]:
    errors = []
    for field in ["firstName", "lastName", "email", "leadSource"]:
        if not data.get(field, "").strip():
            errors.append(f"'{field}' is required.")
    if data.get("email") and "@" not in data["email"]:
        errors.append("'email' must be a valid email address.")
    if data.get("leadSource") and data["leadSource"] not in Config.VALID_LEAD_SOURCES:
        errors.append(f"'leadSource' must be one of: {Config.VALID_LEAD_SOURCES}")
    return errors


# ------------------------------------------------------------------ #
#  Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/score", methods=["POST"])
def score_lead_endpoint():
    """
    Score a lead without creating a CRM record. Used for real-time scoring
    in web forms before submission, or for batch scoring from marketing tools.
    """
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    result = score_lead(
        lead_source=data.get("leadSource", ""),
        job_title=data.get("jobTitle", ""),
        company_size=data.get("companySize", ""),
        industry=data.get("industry", ""),
        deal_value=data.get("dealValue", 0),
        email=data.get("email", ""),
    )
    return jsonify(result), 200


@app.route("/api/leads", methods=["POST"])
def create_lead():
    """
    Create a Contact + Deal from an external lead source.
    Scores the lead, finds the best-fit rep, creates records in Quickbase,
    and triggers the Power Automate intake flow.
    """
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    errors = _validate_lead(data)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 422

    # Deduplicate by email
    existing = qb.find_contact_by_email(data["email"].strip().lower())
    if existing:
        log.info("Duplicate lead email %s — skipping creation", data["email"])
        return jsonify({
            "message":   "Contact already exists.",
            "contactId": existing["contactId"],
            "duplicate": True,
        }), 200

    score_result = score_lead(
        lead_source=data.get("leadSource", ""),
        job_title=data.get("jobTitle", ""),
        company_size=data.get("companySize", ""),
        industry=data.get("industry", ""),
        deal_value=data.get("dealValue", 0),
        email=data["email"],
    )

    reps = qb.get_reps_by_pipeline_load(limit=1)
    rep_record_id = reps[0]["3"]["value"] if reps else None
    rep_name = reps[0]["6"]["value"] if reps else "Unassigned"

    try:
        contact = qb.create_contact(
            first_name=data["firstName"].strip(),
            last_name=data["lastName"].strip(),
            email=data["email"].strip().lower(),
            phone=data.get("phone", ""),
            job_title=data.get("jobTitle", ""),
            contact_type="Lead",
            lead_source=data.get("leadSource", ""),
            lead_score=score_result["score"],
            rep_record_id=rep_record_id,
            notes=data.get("notes", ""),
        )
    except QuickbaseError as exc:
        log.error("Contact creation failed: %s", exc)
        return jsonify({"error": "Failed to create contact.", "detail": str(exc)}), 502

    from datetime import timedelta
    expected_close = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        deal = qb.create_deal(
            deal_name=f"{data['firstName']} {data['lastName']} – {data.get('companyName', '')}",
            contact_record_id=contact["recordId"],
            stage="New Lead",
            deal_value=data.get("dealValue", 0),
            expected_close_date=expected_close,
            lead_source=data.get("leadSource", ""),
            rep_record_id=rep_record_id,
            priority="High" if score_result["score"] >= 75 else ("Medium" if score_result["score"] >= 40 else "Low"),
        )
    except QuickbaseError as exc:
        log.error("Deal creation failed: %s", exc)
        return jsonify({"error": "Contact created but deal creation failed.", "detail": str(exc)}), 502

    qb.log_activity(
        deal_record_id=deal["recordId"],
        contact_record_id=contact["recordId"],
        activity_type="Note",
        subject=f"Lead created via {data.get('leadSource', 'API')}",
        notes=f"Lead score: {score_result['score']} ({score_result['grade']}). Assigned to {rep_name}. Breakdown: {score_result['breakdown']}",
        logged_by="System",
        source="API",
    )

    log.info("Lead created: %s (score=%d) → Deal %s", data["email"], score_result["score"], deal["dealId"])

    return jsonify({
        "contactId":  contact["contactId"],
        "dealId":     deal["dealId"],
        "leadScore":  score_result["score"],
        "leadGrade":  score_result["grade"],
        "assignedTo": rep_name,
        "message":    "Lead created and assigned successfully.",
    }), 201


@app.route("/api/activities", methods=["POST"])
def log_activity():
    """Log a CRM activity from an external system (Jira, Zendesk, custom integrations)."""
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    required = ["dealRecordId", "contactRecordId", "activityType", "subject"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 422

    if data["activityType"] not in Config.VALID_ACTIVITY_TYPES:
        return jsonify({"error": f"Invalid activityType. Valid: {Config.VALID_ACTIVITY_TYPES}"}), 422

    try:
        result = qb.log_activity(
            deal_record_id=data["dealRecordId"],
            contact_record_id=data["contactRecordId"],
            activity_type=data["activityType"],
            subject=data["subject"],
            notes=data.get("notes", ""),
            outcome=data.get("outcome", "Neutral"),
            logged_by=data.get("loggedBy", "API"),
            logged_by_email=data.get("loggedByEmail", "api@system"),
            source="External API",
            follow_up_date=data.get("followUpDate"),
        )
        return jsonify({"result": "Activity logged", "activityId": result.get("data", [{}])[0].get("6", {}).get("value", "")}), 201
    except QuickbaseError as exc:
        return jsonify({"error": "Failed to log activity.", "detail": str(exc)}), 502


@app.route("/api/deals/<int:record_id>/stage", methods=["PATCH"])
def update_deal_stage(record_id: int):
    """Update a deal's pipeline stage from an external system."""
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    new_stage = data.get("stage", "").strip()

    if new_stage not in Config.VALID_STAGES:
        return jsonify({"error": f"Invalid stage. Valid: {Config.VALID_STAGES}"}), 422

    try:
        qb.update_deal_stage(record_id, new_stage, data.get("notes", ""))
        return jsonify({"recordId": record_id, "newStage": new_stage, "updated": True}), 200
    except QuickbaseError as exc:
        return jsonify({"error": "Failed to update stage.", "detail": str(exc)}), 502


@app.route("/api/sync/activities", methods=["POST"])
def trigger_activity_sync():
    """Manually trigger the Graph API email/calendar sync."""
    if not _verify_signature(request):
        return jsonify({"error": "Unauthorized."}), 401

    reps_data = qb.get_reps_by_pipeline_load(limit=50)
    reps = [{"email": r["7"]["value"], "name": r["6"]["value"]} for r in reps_data if r.get("7", {}).get("value")]

    from email_tracker import run_activity_sync
    summary = run_activity_sync(reps)
    return jsonify({"result": "Sync complete", "summary": summary}), 200


# ------------------------------------------------------------------ #
#  Error handlers                                                     #
# ------------------------------------------------------------------ #

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404

@app.errorhandler(500)
def internal_error(e):
    log.exception("Unhandled exception")
    return jsonify({"error": "An internal server error occurred."}), 500


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone="Africa/Johannesburg")

    def _scheduled_sync():
        try:
            reps_data = qb.get_reps_by_pipeline_load(limit=50)
            reps = [{"email": r["7"]["value"], "name": r["6"]["value"]}
                    for r in reps_data if r.get("7", {}).get("value")]
            from email_tracker import run_activity_sync
            run_activity_sync(reps)
        except Exception as exc:
            log.error("Scheduled sync failed: %s", exc)

    scheduler.add_job(_scheduled_sync, "interval", minutes=30, id="graph_sync")
    scheduler.start()
    log.info("CRM webhook server starting on port %d", Config.PORT)

    try:
        app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
    finally:
        scheduler.shutdown()
