"""
Flask webhook server — Digital Transformation Case Study.

Endpoints:
  POST /api/transformation/snapshot        — run ROI calc, store snapshot, send report
  POST /api/transformation/impact          — run impact analysis on all baselines
  POST /api/transformation/baseline/seed   — seed the Meridian baseline metrics
  POST /api/transformation/baseline/after  — record an after-state measurement
  GET  /api/transformation/roi             — return current ROI as JSON
  GET  /api/transformation/report          — return current HTML report
  GET  /health

Run:
  python webhook_handler.py
"""

import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify, Response

from config import Config
from roi_calculator import compute as compute_roi
from impact_analyzer import analyze
from report_generator import build_html, get_subject
from baseline_collector import record_after_metric, seed_meridian_baselines

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)

_QB_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _verify(req) -> bool:
    sig = req.headers.get("X-Webhook-Signature", "")
    if not sig:
        return False
    expected = hmac.new(
        Config.WEBHOOK_SECRET.encode(), req.get_data(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", sig)


def _trigger_pa_flow(url: str, payload: dict) -> bool:
    if not url:
        return False
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok
    except Exception as exc:
        log.warning("PA flow trigger failed: %s", exc)
        return False


def _write_monthly_snapshot(roi_data, period: str) -> bool:
    """Write the monthly ROI snapshot to Quickbase."""
    try:
        requests.post("https://api.quickbase.com/v1/records",
                      headers=_QB_HEADERS,
                      json={"to": Config.QB_ROI_MONTHLY_TABLE, "data": [{
                          "7":  {"value": period},
                          "8":  {"value": roi_data.total_actual_ytd},
                          "9":  {"value": roi_data.total_projected_ytd},
                          "10": {"value": roi_data.program_roi_pct},
                          "11": {"value": roi_data.program_payback_months},
                          "12": {"value": roi_data.program_npv_3yr},
                          "13": {"value": roi_data.benefit_realization_pct},
                          "14": {"value": roi_data.realization_status},
                          "15": {"value": roi_data.snapshot_time},
                      }]}, timeout=10)
        return True
    except Exception as exc:
        log.error("QB snapshot write failed: %s", exc)
        return False


# ------------------------------------------------------------------ #
#  Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/transformation/snapshot", methods=["POST"])
def create_snapshot():
    """
    Run the full ROI calculation, write the monthly snapshot, trigger the report.
    Called by Power Automate flow 01 on the 1st of each month.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized"}), 401

    data   = request.get_json(silent=True) or {}
    period = data.get("period", datetime.now(timezone.utc).strftime("%Y-%m"))

    # Fetch actual benefits from QB if available; otherwise use projections
    actual_benefits = data.get("actualBenefitsByInitiative")

    roi = compute_roi(actual_benefits_by_initiative=actual_benefits)
    impact = analyze()
    html   = build_html(roi, impact)
    subject = get_subject(roi)

    # Save to QB
    _write_monthly_snapshot(roi, period)

    # Trigger PA report flow
    _trigger_pa_flow(Config.PA_MONTHLY_REPORT_URL, {
        "reportHtml":            html,
        "reportSubject":         subject,
        "totalBenefitsYTD":      roi.total_actual_ytd,
        "totalInvestment":       roi.total_investment,
        "roiPct":                roi.program_roi_pct,
        "paybackMonths":         roi.program_payback_months,
        "npv3Year":              roi.program_npv_3yr,
        "benefitRealizationPct": roi.benefit_realization_pct,
        "milestonesCompleted":   impact.get("summary", {}).get("targetsMet", 0),
        "milestonesTotal":       impact.get("summary", {}).get("totalMetrics", 0),
        "alertCount":            sum(1 for i in roi.initiative_rois if i.realization_status == "Underperforming"),
    })

    # Trigger benefit alerts for underperforming initiatives
    for init in roi.initiative_rois:
        if init.realization_status == "Underperforming":
            _trigger_pa_flow(Config.PA_BENEFIT_ALERT_URL, {
                "initiativeId":          init.initiative_id,
                "initiativeName":        init.name,
                "ownerEmail":            "owner@yourcompany.com",  # resolved from QB in production
                "ownerName":             "Initiative Owner",
                "benefitRealizationPct": init.realization_pct,
                "projectedBenefitsYTD":  init.projected_ytd,
                "actualBenefitsYTD":     init.actual_ytd,
                "gapAmount":             init.projected_ytd - init.actual_ytd,
                "realizationStatus":     init.realization_status,
                "topUnderachievingMetric": "Review domain metrics in dashboard",
            })

    return jsonify({
        "period":          period,
        "roiPct":          roi.program_roi_pct,
        "paybackMonths":   roi.program_payback_months,
        "npv3Year":        roi.program_npv_3yr,
        "realization":     roi.benefit_realization_pct,
        "status":          roi.realization_status,
        "reportGenerated": True,
    }), 200


@app.route("/api/transformation/roi", methods=["GET"])
def get_roi():
    """Return the current ROI calculation as JSON."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized"}), 401

    roi = compute_roi()
    return jsonify({
        "snapshotTime":          roi.snapshot_time,
        "totalInvestment":       roi.total_investment,
        "totalActualAnnual":     roi.total_actual_annual,
        "totalActualYTD":        roi.total_actual_ytd,
        "programROIPct":       roi.program_roi_pct,
        "paybackMonths":         roi.program_payback_months,
        "npv3Year":              roi.program_npv_3yr,
        "benefitRealization":    roi.benefit_realization_pct,
        "realizationStatus":     roi.realization_status,
        "sensitivity":           roi.sensitivity,
        "initiativeRois": [
            {
                "id":          i.initiative_id,
                "name":        i.name,
                "domain":      i.domain,
                "roiPct":      i.roi_pct,
                "payback":     i.payback_months,
                "npv":         i.npv_3yr,
                "realization": i.realization_pct,
                "status":      i.realization_status,
            }
            for i in roi.initiative_rois
        ],
    }), 200


@app.route("/api/transformation/report", methods=["GET"])
def get_report_html():
    """Return the current HTML report. Useful for browser preview."""
    if not _verify(request):
        return Response("Unauthorized", status=401)

    roi    = compute_roi()
    impact = analyze()
    html   = build_html(roi, impact)
    return Response(html, mimetype="text/html")


@app.route("/api/transformation/impact", methods=["POST"])
def get_impact():
    """Run the impact analysis and return the before/after comparison."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized"}), 401

    data   = request.get_json(silent=True) or {}
    result = analyze(data.get("initiativeRecordId"))
    return jsonify(result), 200


@app.route("/api/transformation/baseline/seed", methods=["POST"])
def seed_baselines():
    """
    Seed all Meridian baselines into Quickbase.
    Requires a mapping of initiative name → QB record ID in the body.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized"}), 401

    mapping = request.get_json(silent=True) or {}
    if not mapping:
        return jsonify({"error": "Body must be {\"Initiative Name\": qb_record_id}"}), 422

    seed_meridian_baselines(mapping)
    return jsonify({"result": "Baselines seeded", "count": len(mapping)}), 201


@app.route("/api/transformation/baseline/after", methods=["PATCH"])
def update_after_metric():
    """Record an after-state measurement for a specific baseline metric."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    required = ["baselineRecordId", "afterValue", "measuredBy"]
    missing  = [f for f in required if not data.get(f) and data.get(f) != 0]
    if missing:
        return jsonify({"error": f"Missing: {missing}"}), 422

    record_after_metric(
        baseline_record_id = int(data["baselineRecordId"]),
        after_value        = float(data["afterValue"]),
        measured_by        = data["measuredBy"],
        measurement_notes  = data.get("notes", ""),
    )
    return jsonify({"result": "After-state recorded", "recordId": data["baselineRecordId"]}), 200


# ------------------------------------------------------------------ #
#  Error handlers                                                     #
# ------------------------------------------------------------------ #

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    log.exception("Unhandled exception")
    return jsonify({"error": "An internal server error occurred"}), 500


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    log.info("Transformation Intelligence Platform starting on port %d", Config.PORT)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
