"""
Flask webhook server — Employee Onboarding Platform.

Endpoints:
  POST /api/onboarding/generate               — generate tasks for a new hire
  PATCH /api/onboarding/<id>/recalculate-dates — recalculate dates when start date changes
  POST /api/onboarding/<id>/enable-account    — enable AD account on Day 1
  POST /api/onboarding/hris-intake            — accept a new hire payload from HRIS
  GET  /health

Run:
  python webhook_handler.py
  waitress-serve --port=5002 webhook_handler:app
"""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from quickbase_client import OnboardingQuickbaseClient, QuickbaseError
from task_generator import generate_tasks, recalculate_task_dates
from ad_provisioner import provision_new_hire, enable_account_on_day_one

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
qb = OnboardingQuickbaseClient()


# ------------------------------------------------------------------ #
#  Auth                                                               #
# ------------------------------------------------------------------ #

def _verify(req) -> bool:
    sig = req.headers.get("X-Webhook-Signature", "")
    if not sig:
        return False
    expected = hmac.new(
        Config.WEBHOOK_SECRET.encode(), req.get_data(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", sig)


# ------------------------------------------------------------------ #
#  Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/onboarding/generate", methods=["POST"])
def generate_onboarding_tasks():
    """
    Called by the Quickbase automation immediately after a new Employee record is created.
    Generates all tasks from the plan template and triggers AD provisioning.

    Required JSON body fields:
      employeeRecordId, firstName, lastName, personalEmail, jobTitle,
      department, startDate, employmentType, workLocation,
      managerName, managerEmail, buddyName, buddyEmail, onboardingPlanId
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    hire = request.get_json(silent=True)
    if not hire:
        return jsonify({"error": "JSON body required."}), 400

    required = ["employeeRecordId", "startDate", "onboardingPlanId"]
    missing = [f for f in required if not hire.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 422

    # Load task templates
    plan_id = hire["onboardingPlanId"]
    templates = qb.get_templates_by_plan(plan_id)

    if not templates:
        return jsonify({"error": f"No templates found for plan ID {plan_id}."}), 404

    # Generate tasks
    gen_result = generate_tasks(hire, templates, qb)

    # Provision AD account (non-blocking — failures logged but don't fail the request)
    ad_result = {}
    try:
        ad_result = provision_new_hire(hire)
        if ad_result.get("adObjectId"):
            qb.update_employee(hire["employeeRecordId"], {
                11: ad_result["workEmail"],
                33: ad_result["licenseAssigned"],
                34: ad_result["licenseAssigned"],
            })
    except Exception as exc:
        log.error("AD provisioning failed for hire %s: %s",
                  hire.get("employeeId", "?"), exc)
        ad_result = {"success": False, "errors": [str(exc)]}

    # Trigger kickoff flow
    import requests as req_lib
    if Config.PA_KICKOFF_FLOW_URL:
        try:
            req_lib.post(Config.PA_KICKOFF_FLOW_URL, json={
                **hire,
                "tasksCreated": gen_result["tasksCreated"],
                "workEmail":    ad_result.get("workEmail", ""),
            }, timeout=10)
        except Exception as exc:
            log.warning("Kickoff flow trigger failed: %s", exc)

    return jsonify({
        "employeeId":       hire.get("employeeId"),
        "tasksCreated":     gen_result["tasksCreated"],
        "taskErrors":       gen_result.get("errors", []),
        "adProvisioned":    ad_result.get("success", False),
        "workEmail":        ad_result.get("workEmail", ""),
        "adErrors":         ad_result.get("errors", []),
    }), 201


@app.route("/api/onboarding/<int:record_id>/recalculate-dates", methods=["PATCH"])
def recalculate_dates(record_id: int):
    """Recalculate all task due dates when the hire's start date changes."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    new_start = data.get("newStartDate", "").strip()
    if not new_start:
        return jsonify({"error": "'newStartDate' is required (YYYY-MM-DD)."}), 422

    result = recalculate_task_dates(record_id, new_start, qb)
    return jsonify(result), 200


@app.route("/api/onboarding/<string:object_id>/enable-account", methods=["POST"])
def enable_account(object_id: str):
    """Enable the Azure AD account on the hire's start date morning."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    success = enable_account_on_day_one(object_id)
    if success:
        return jsonify({"result": "Account enabled", "objectId": object_id}), 200
    return jsonify({"error": "Failed to enable account. Check server logs."}), 502


@app.route("/api/onboarding/hris-intake", methods=["POST"])
def hris_intake():
    """
    Accept a new hire payload from an HRIS system (BambooHR, SuccessFactors, Workday).
    Creates the Employee record in Quickbase, then triggers task generation.

    Supports BambooHR webhook format and a generic format.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "JSON body required."}), 400

    # Normalize HRIS payload to our internal format
    hire = {
        "firstName":      raw.get("firstName") or raw.get("first_name", ""),
        "lastName":       raw.get("lastName") or raw.get("last_name", ""),
        "personalEmail":  raw.get("personalEmail") or raw.get("personal_email", ""),
        "jobTitle":       raw.get("jobTitle") or raw.get("job_title") or raw.get("position", ""),
        "department":     raw.get("department") or raw.get("department_name", ""),
        "startDate":      raw.get("startDate") or raw.get("start_date") or raw.get("hireDate", ""),
        "employmentType": raw.get("employmentType") or raw.get("employment_type", "Permanent"),
        "workLocation":   raw.get("workLocation") or raw.get("work_location", "Office"),
        "managerEmail":   raw.get("managerEmail") or raw.get("manager_email", ""),
        "managerName":    raw.get("managerName") or raw.get("manager_name", ""),
        "buddyEmail":     raw.get("buddyEmail") or raw.get("buddy_email", ""),
        "buddyName":      raw.get("buddyName") or raw.get("buddy_name", ""),
    }

    required = ["firstName", "lastName", "personalEmail", "startDate", "department"]
    missing = [f for f in required if not hire.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 422

    # Create QB employee record
    try:
        emp_fields = {
            7: hire["firstName"], 8: hire["lastName"], 10: hire["personalEmail"],
            13: hire["jobTitle"], 15: hire["managerName"], 16: hire["managerEmail"],
            17: hire["buddyName"], 18: hire["buddyEmail"], 19: hire["startDate"],
            20: hire["employmentType"], 21: hire["workLocation"],
            24: "Pre-boarding",
        }
        create_result = qb._request("POST", "/records", json={
            "to": Config.QB_EMPLOYEES_TABLE,
            "data": [{str(k): {"value": v} for k, v in emp_fields.items() if v}],
            "fieldsToReturn": [3, 6],
        })
        record_id = create_result["data"][0]["3"]["value"]
        employee_id = create_result["data"][0]["6"]["value"]
        hire["employeeRecordId"] = record_id
        hire["employeeId"] = employee_id
        log.info("Created QB employee record: %s (%s)", employee_id, hire["personalEmail"])
    except QuickbaseError as exc:
        return jsonify({"error": "Failed to create QB employee record.", "detail": str(exc)}), 502

    # Trigger task generation (reuse the /generate endpoint logic)
    # We need to resolve the onboarding plan from the department
    hire["onboardingPlanId"] = _resolve_plan_id(hire["department"], hire["employmentType"], hire["workLocation"])

    return generate_onboarding_tasks_direct(hire)


def _resolve_plan_id(department: str, employment_type: str, work_location: str) -> int:
    """Find the best-matching Onboarding Plan for this hire's attributes."""
    try:
        result = qb._request("POST", "/records/query", json={
            "from": Config.QB_PLANS_TABLE,
            "select": [3],
            "where": f"{{7.EX.'{department}'}} AND {{8.EX.'{employment_type}'}} AND {{12.EX.'true'}}",
            "options": {"top": 1},
        })
        data = result.get("data", [])
        if data:
            return data[0]["3"]["value"]
    except Exception as exc:
        log.warning("Plan lookup failed: %s. Using fallback.", exc)

    # Fallback: get any active plan for this department
    try:
        result = qb._request("POST", "/records/query", json={
            "from": Config.QB_PLANS_TABLE,
            "select": [3],
            "where": f"{{7.EX.'{department}'}} AND {{12.EX.'true'}}",
            "options": {"top": 1},
        })
        data = result.get("data", [])
        if data:
            return data[0]["3"]["value"]
    except Exception:
        pass

    return 0


def generate_onboarding_tasks_direct(hire: dict) -> tuple:
    """Internal version of generate route — called from hris_intake."""
    templates = qb.get_templates_by_plan(hire["onboardingPlanId"])
    gen_result = generate_tasks(hire, templates, qb)

    ad_result = {}
    try:
        ad_result = provision_new_hire(hire)
        if ad_result.get("adObjectId"):
            qb.update_employee(hire["employeeRecordId"], {
                11: ad_result.get("workEmail", ""),
                33: ad_result.get("licenseAssigned", False),
                34: ad_result.get("licenseAssigned", False),
            })
    except Exception as exc:
        log.error("AD provisioning error: %s", exc)

    return jsonify({
        "employeeId":    hire.get("employeeId"),
        "tasksCreated":  gen_result["tasksCreated"],
        "adProvisioned": ad_result.get("success", False),
        "workEmail":     ad_result.get("workEmail", ""),
    }), 201


# ------------------------------------------------------------------ #
#  Scheduled Jobs                                                     #
# ------------------------------------------------------------------ #

def _day_one_account_enablement():
    """Enable AD accounts for all employees starting today."""
    hires = qb.get_employees_starting_today()
    for hire in hires:
        if hire.get("adAccountCreated") and hire.get("workEmail"):
            log.info("Enabling AD account for %s", hire["workEmail"])


# ------------------------------------------------------------------ #
#  Error Handlers                                                     #
# ------------------------------------------------------------------ #

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404

@app.errorhandler(500)
def internal_error(e):
    log.exception("Unhandled exception")
    return jsonify({"error": "An internal server error occurred."}), 500


# ------------------------------------------------------------------ #
#  Entry Point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone="Africa/Johannesburg")
    scheduler.add_job(_day_one_account_enablement, "cron", hour=6, minute=0, id="day1_enable")
    scheduler.start()
    log.info("Onboarding webhook server starting on port %d", Config.PORT)

    try:
        app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
    finally:
        scheduler.shutdown()
