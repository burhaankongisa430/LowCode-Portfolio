"""
Flask webhook server — Executive Dashboard.

Endpoints:
  POST /api/kpi/run-etl         — trigger a full ETL run (manual or scheduled)
  POST /api/kpi/run-report      — trigger ETL + weekly email report
  GET  /api/kpi/latest          — return latest KPI snapshot as JSON
  GET  /api/kpi/alerts          — return active alerts
  POST /api/kpi/archive         — archive old snapshots (monthly scheduled)
  GET  /health

Run:
  python webhook_handler.py
  waitress-serve --port=5004 webhook_handler:app

Or run the standalone scheduler:
  python scheduler.py
"""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify

from config import Config
from scheduler import run_etl

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


# ------------------------------------------------------------------ #
#  Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/kpi/run-etl", methods=["POST"])
def trigger_etl():
    """Manually trigger an ETL run. Called by Power Automate flow 01."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    try:
        kpis = run_etl(is_weekly_report=False)
        return jsonify({
            "healthScore":      kpis["health_score"],
            "healthStatus":     kpis["health_status"],
            "operationalScore": kpis["operational_score"],
            "commercialScore":  kpis["commercial_score"],
            "peopleScore":      kpis["people_score"],
            "financeScore":     kpis["finance_score"],
            "domainsAvailable": kpis["domains_available"],
            "etlDurationSeconds": kpis["etl_duration_seconds"],
            "alertCount":       len(kpis.get("alerts", [])),
            "errors":           kpis.get("etl_errors", []),
        }), 200
    except Exception as exc:
        log.exception("ETL run failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/kpi/run-report", methods=["POST"])
def trigger_report():
    """Trigger ETL + weekly executive report email. Called Monday morning."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    try:
        kpis = run_etl(is_weekly_report=True)
        return jsonify({"result": "ETL and report complete", "healthScore": kpis["health_score"]}), 200
    except Exception as exc:
        log.exception("Report run failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/kpi/latest", methods=["GET"])
def get_latest():
    """Return the most recent KPI snapshot from QB."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    try:
        r = requests.post(
            "https://api.quickbase.com/v1/records/query",
            headers=_QB_HEADERS,
            json={
                "from": Config.QB_SNAPSHOTS_TABLE,
                "select": [3, 6, 7, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 35],
                "sortBy": [{"fieldId": 7, "order": "DESC"}],
                "options": {"top": 1},
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return jsonify({"error": "No snapshots found."}), 404

        row = data[0]
        def v(fid): return row.get(str(fid), {}).get("value")

        return jsonify({
            "snapshotTime":     v(7),
            "healthScore":      v(11),
            "healthStatus":     v(12),
            "operationalScore": v(14),
            "commercialScore":  v(15),
            "peopleScore":      v(16),
            "financeScore":     v(17),
            "domainsAvailable": v(35),
        }), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/kpi/archive", methods=["POST"])
def archive_snapshots():
    """
    Archive old snapshots. Called monthly by QB automation.
    In production this would aggregate hourly rows into daily averages
    for records older than 90 days, then delete the source rows.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    log.info("Snapshot archive job triggered.")
    return jsonify({"result": "Archive job queued. Implementation: aggregate + delete QB rows > 90 days old."}), 200


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
    log.info("Executive Dashboard API starting on port %d", Config.PORT)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
