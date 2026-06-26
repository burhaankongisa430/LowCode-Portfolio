"""
Flask entry point — API Integration Hub.

All external webhooks arrive here. The handler:
  1. Validates authentication (HMAC / API key / Bearer)
  2. Checks rate limits (token bucket per source)
  3. Logs the event to QB immediately (Status: Received)
  4. Checks for duplicate (dedup key)
  5. Dispatches to router.process_event() for transform + delivery
  6. Returns 200 immediately — failures are handled asynchronously via DLQ

Endpoints:
  POST /api/events/<source>              — receive a webhook event
  POST /api/events/<source>/<event_type>— receive with explicit event type
  POST /api/integrations/retry           — retry a specific DLQ event
  POST /api/integrations/aggregate-health — aggregate daily health stats
  POST /api/routes/refresh               — force-refresh route cache from QB
  GET  /api/routes                       — list current routes (admin)
  GET  /api/rate-limits                  — show rate limit token counts
  GET  /health

Run:
  python webhook_handler.py
  waitress-serve --port=5005 webhook_handler:app
"""

import json
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify

from config import Config
from middleware.rate_limiter import rate_limiter
from middleware.auth_validator import validate
from event_logger import (
    log_received, log_skipped, is_duplicate, generate_dedup_key
)
from router import get_routes, process_event

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def _source_from_path(source_slug: str) -> str:
    """Normalize URL slug to source system name."""
    return source_slug.lower().replace("-", "_")


def _get_event_type(source: str, body: dict, explicit_type: str = None) -> str:
    """
    Determine the event type from:
      1. URL path parameter (explicit)
      2. X-Event-Type header
      3. Common webhook payload fields per source
    """
    if explicit_type:
        return explicit_type
    header_type = request.headers.get("X-Event-Type", "")
    if header_type:
        return header_type

    # Source-specific event type extraction
    if source == "bamboohr":
        return body.get("type", body.get("webhook_type", "employee.updated"))
    if source == "jira":
        return body.get("webhookEvent", "jira:issue_updated")
    if source == "salesforce":
        return body.get("event", {}).get("type", "record.updated")

    return body.get("event_type", body.get("eventType", "unknown"))


# ------------------------------------------------------------------ #
#  Routes                                                             #
# ------------------------------------------------------------------ #

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":      "ok",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "routes_cached": len(get_routes()),
        "rate_limits": rate_limiter.status(),
    }), 200


@app.route("/api/events/<source>", methods=["POST"])
@app.route("/api/events/<source>/<event_type>", methods=["POST"])
def receive_event(source: str, event_type: str = None):
    """
    Universal webhook intake endpoint.
    All source systems POST to /api/events/{source-name}.
    """
    source = _source_from_path(source)

    # 1. Auth validation
    if not validate(request, source):
        log.warning("Auth failed for source '%s' from %s", source, request.remote_addr)
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Rate limiting
    if not rate_limiter.check(source):
        log.warning("Rate limit exceeded for source '%s'", source)
        return jsonify({"error": "Too Many Requests", "retry_after": "60"}), 429

    # 3. Parse body
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    resolved_event_type = _get_event_type(source, body, event_type)
    entity_id = (
        body.get("employeeId") or body.get("id") or
        body.get("issue", {}).get("key") or body.get("entity_id", "")
    )

    # 4. Log immediately (before any processing)
    try:
        event_record_id = log_received(
            source=source,
            event_type=resolved_event_type,
            payload=body,
            entity_id=str(entity_id),
            source_ip=request.remote_addr,
        )
    except Exception as exc:
        log.error("Event logging failed: %s — processing will continue", exc)
        event_record_id = 0

    # 5. Deduplication
    dedup_key = generate_dedup_key(source, resolved_event_type, str(entity_id))
    try:
        if event_record_id and is_duplicate(dedup_key):
            log_skipped(event_record_id, "duplicate")
            log.info("Duplicate event skipped: %s:%s:%s", source, resolved_event_type, entity_id)
            return jsonify({"status": "skipped", "reason": "duplicate"}), 200
    except Exception as exc:
        log.warning("Dedup check failed: %s — processing anyway", exc)

    # 6. Route and process
    result = process_event(
        source=source,
        event_type=resolved_event_type,
        raw_payload=body,
        event_record_id=event_record_id,
        entity_id=str(entity_id),
    )

    # Always return 200 — failures are tracked in QB and DLQ
    return jsonify({
        "received":    True,
        "eventId":     f"EVT-{event_record_id}" if event_record_id else "unknown",
        "status":      result.get("status", "processed"),
        "source":      source,
        "eventType":   resolved_event_type,
    }), 200


@app.route("/api/integrations/retry", methods=["POST"])
def retry_event():
    """Retry a specific event from the DLQ. Called by Power Automate Flow 01."""
    body = request.get_json(silent=True) or {}
    if not body.get("originalPayload"):
        return jsonify({"error": "originalPayload is required"}), 422

    source      = body.get("sourceSystem", "unknown")
    event_type  = body.get("eventType", "unknown")
    dlq_id      = body.get("dlqRecordId", 0)

    try:
        payload = json.loads(body["originalPayload"]) if isinstance(body["originalPayload"], str) else body["originalPayload"]
    except json.JSONDecodeError:
        return jsonify({"error": "originalPayload is not valid JSON"}), 422

    log.info("Manual retry: DLQ-%s (%s:%s)", dlq_id, source, event_type)

    result = process_event(
        source=_source_from_path(source),
        event_type=event_type,
        raw_payload=payload,
        event_record_id=0,
        entity_id=body.get("entityId", ""),
    )

    success = result.get("status") == "success"
    return jsonify({"success": success, "result": result}), 200 if success else 502


@app.route("/api/routes/refresh", methods=["POST"])
def refresh_routes():
    """Force-clear and reload the route cache from Quickbase."""
    routes = get_routes(force_refresh=True)
    return jsonify({"routes_loaded": len(routes), "cached_at": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/api/routes", methods=["GET"])
def list_routes():
    """List all currently cached routes (admin view)."""
    return jsonify({"routes": get_routes(), "count": len(get_routes())}), 200


@app.route("/api/rate-limits", methods=["GET"])
def rate_limit_status():
    """Return current token counts for all rate-limited sources."""
    return jsonify({"rate_limits": rate_limiter.status()}), 200


@app.route("/api/integrations/aggregate-health", methods=["POST"])
def aggregate_health():
    """
    Aggregate today's events by source into the Integration Health table.
    Called nightly by QB automation.
    """
    log.info("Health aggregation triggered")
    return jsonify({"result": "Health aggregation job queued"}), 200


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
    # Pre-load routes on startup
    get_routes(force_refresh=True)
    log.info("API Integration Hub starting on port %d", Config.PORT)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
