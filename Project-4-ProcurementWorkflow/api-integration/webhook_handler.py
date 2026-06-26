"""
Flask webhook server — Procurement Approval System.

Endpoints:
  POST /api/procurement/validate          — budget + vendor check (called by PA flow 01)
  POST /api/procurement/generate-po       — generate PO and sync to ERP (called by PA flow 03)
  POST /api/procurement/budget-release    — release budget commitment on rejection
  POST /api/procurement/erp-sync         — push a PO to ERP (called by QB Pipeline)
  GET  /api/procurement/request/<id>      — get request details
  GET  /health

Run:
  python webhook_handler.py
  waitress-serve --port=5003 webhook_handler:app
"""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify

from config import Config
from quickbase_client import ProcurementQBClient, QuickbaseError
from budget_validator import validate as validate_budget, release_budget_commitment
from po_generator import generate_and_save
from erp_connector import ERPConnector

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
qb = ERPConnector()
qb_client = ProcurementQBClient()
erp = ERPConnector()


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


@app.route("/api/procurement/validate", methods=["POST"])
def validate_request():
    """
    Called by Power Automate flow 01 immediately after request submission.
    Checks budget availability and vendor approval status.
    Reserves the budget commitment atomically.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    required = ["departmentId", "requestAmount"]
    missing = [f for f in required if not data.get(f) and data.get(f) != 0]
    if missing:
        return jsonify({"error": f"Missing: {missing}"}), 422

    result = validate_budget(
        department_record_id=int(data["departmentId"]),
        request_amount=float(data["requestAmount"]),
        vendor_record_id=int(data.get("vendorId", 0) or 0),
    )
    return jsonify(result), 200


@app.route("/api/procurement/generate-po", methods=["POST"])
def generate_po():
    """
    Called by Power Automate flow 03 after all approval levels pass.
    Generates the PO HTML, saves to QB, syncs to ERP, returns PO details.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    required = ["requestRecordId", "requestNumber", "totalAmount", "approvedBy"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {missing}"}), 422

    # Generate PO document and QB record
    try:
        po_result = generate_and_save(data, qb_client)
    except Exception as exc:
        log.error("PO generation failed: %s", exc)
        return jsonify({"error": "PO generation failed.", "detail": str(exc)}), 502

    # Sync to ERP
    erp_result = erp.sync_po({
        **data,
        "poNumber": po_result["poNumber"],
        "amount":   data["totalAmount"],
        "issueDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })

    # Write ERP reference back to QB if sync succeeded
    if erp_result["synced"] and erp_result.get("erpReference"):
        try:
            qb_client.update_po_erp_reference(po_result["poRecordId"], erp_result["erpReference"])
        except Exception as exc:
            log.warning("ERP ref write-back failed: %s", exc)

    log.info("PO generated: %s | ERP sync: %s", po_result["poNumber"], erp_result["synced"])

    return jsonify({
        "poNumber":     po_result["poNumber"],
        "poRecordId":   po_result["poRecordId"],
        "poHtml":       po_result["poHtml"],
        "erpReference": erp_result.get("erpReference", ""),
        "erpSynced":    erp_result["synced"],
    }), 201


@app.route("/api/procurement/budget-release", methods=["POST"])
def budget_release():
    """
    Called by Power Automate flow 04 (rejection) or a cancellation automation.
    Releases the reserved budget commitment.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    if not data.get("requestRecordId") or not data.get("totalAmount"):
        return jsonify({"error": "requestRecordId and totalAmount are required."}), 422

    # Get department ID from the request record
    req = qb_client.get_request(int(data["requestRecordId"]))
    if not req:
        return jsonify({"error": "Request not found."}), 404

    # Fetch department record ID from budget code field (field 11 links to budget codes)
    # In practice, this comes from the QB request record's department link
    dept_id = data.get("departmentId", 0)
    if not dept_id:
        return jsonify({"error": "departmentId is required for budget release."}), 422

    released = release_budget_commitment(int(dept_id), float(data["totalAmount"]))
    return jsonify({"released": released, "amount": data["totalAmount"]}), 200


@app.route("/api/procurement/erp-sync", methods=["POST"])
def erp_sync():
    """
    Called by the Quickbase Pipeline when a PO record is created.
    Pushes the PO to the ERP system.
    """
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    if not data.get("poNumber"):
        return jsonify({"error": "poNumber is required."}), 422

    result = erp.sync_po(data)
    return jsonify(result), 200 if result["synced"] else 502


@app.route("/api/procurement/request/<int:record_id>", methods=["GET"])
def get_request(record_id: int):
    """Fetch a purchase request by QB record ID."""
    if not _verify(request):
        return jsonify({"error": "Unauthorized."}), 401

    req = qb_client.get_request(record_id)
    if not req:
        return jsonify({"error": f"Request {record_id} not found."}), 404
    return jsonify(req), 200


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
    log.info("Procurement API server starting on port %d", Config.PORT)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
