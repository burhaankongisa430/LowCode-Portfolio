"""
Config-driven event routing engine.

Loads routing rules from the Quickbase Integration Routes table.
For each inbound event, finds the matching route and dispatches to
the correct transformer + connector pair.

Routes are cached in memory for 5 minutes to avoid a QB API call
on every event. The cache is invalidated by the /api/routes/refresh endpoint.
"""

import json
import logging
import time
from typing import Any
import requests
from config import Config

log = logging.getLogger(__name__)

# Module-level route cache
_route_cache: list[dict] = []
_cache_loaded_at: float  = 0
_CACHE_TTL_SECONDS        = 300  # 5 minutes


def _qb_headers() -> dict:
    return {
        "QB-Realm-Hostname": Config.QB_REALM,
        "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
        "Content-Type":      "application/json",
    }


def _load_routes() -> list[dict]:
    """Fetch all active routes from Quickbase."""
    r = requests.post(
        "https://api.quickbase.com/v1/records/query",
        headers=_qb_headers(),
        json={
            "from": Config.QB_ROUTES_TABLE,
            "select": [3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            "where": "{15.EX.'true'}",
            "sortBy": [{"fieldId": 16, "order": "ASC"}],
            "options": {"top": 100},
        },
        timeout=10,
    )
    r.raise_for_status()
    routes = []
    for row in r.json().get("data", []):
        def v(fid): return row.get(str(fid), {}).get("value")
        mapping_raw = v(14) or "{}"
        try:
            mapping = json.loads(mapping_raw) if isinstance(mapping_raw, str) else mapping_raw
        except json.JSONDecodeError:
            mapping = {}

        routes.append({
            "route_id":     v(6),
            "route_name":   v(7),
            "source":       (v(8) or "").lower().replace(" ", "_"),
            "event_type":   v(9) or "*",
            "target":       (v(10) or "").lower().replace(" ", "_"),
            "target_action":v(11) or "create_record",
            "target_table": v(12) or "",
            "transformer":  v(13) or "generic_transformer",
            "mapping":      mapping,
            "priority":     int(v(16) or 99),
            "max_retries":  int(v(17) or Config.MAX_RETRIES),
            "timeout":      int(v(18) or 15),
        })
    log.info("Loaded %d active routes from Quickbase", len(routes))
    return routes


def get_routes(force_refresh: bool = False) -> list[dict]:
    """Return cached routes, refreshing if cache is stale or forced."""
    global _route_cache, _cache_loaded_at
    if force_refresh or (time.monotonic() - _cache_loaded_at) > _CACHE_TTL_SECONDS:
        try:
            _route_cache   = _load_routes()
            _cache_loaded_at = time.monotonic()
        except Exception as exc:
            log.error("Failed to load routes: %s — using cached routes.", exc)
    return _route_cache


def find_route(source: str, event_type: str) -> dict | None:
    """
    Find the first matching route for a given source + event_type combination.
    Supports wildcard event_type="*" to match any event from that source.
    """
    source_key = source.lower().replace(" ", "_").replace("-", "_")
    routes = get_routes()
    for route in routes:
        source_match = route["source"] == source_key
        event_match  = route["event_type"] in ("*", event_type)
        if source_match and event_match:
            return route
    return None


def dispatch(route: dict, transformed_payload: dict) -> dict:
    """
    Send the transformed payload to the target system using the correct connector.
    Returns a result dict with status and any target entity ID.
    """
    from connectors import quickbase_connector, jira_connector, teams_connector

    target = route["target"]
    target_payload = {
        **transformed_payload,
        "action":       route["target_action"],
        "target_table": route["target_table"],
    }

    if target == "quickbase":
        return quickbase_connector.send(target_payload)

    if target == "jira":
        return jira_connector.send(target_payload)

    if target in ("teams", "microsoft_teams"):
        return teams_connector.send(target_payload)

    raise ValueError(f"No connector registered for target '{target}'")


def transform_payload(route: dict, raw_payload: dict, source: str, event_type: str) -> dict:
    """Apply the appropriate transformer based on the route config."""
    from transformers import bamboohr_transformer, jira_transformer, generic_transformer

    transformer_name = route.get("transformer", "generic_transformer")

    if transformer_name == "bamboohr_transformer":
        return bamboohr_transformer.transform(raw_payload, event_type)

    if transformer_name == "jira_transformer":
        return jira_transformer.transform(raw_payload, event_type)

    # Default: generic field mapping transformer
    mapping = route.get("mapping", {})
    if not mapping:
        log.warning("Route %s uses generic_transformer but has no mapping config",
                    route.get("route_id"))
    return generic_transformer.transform(raw_payload, mapping)


def process_event(source: str, event_type: str, raw_payload: dict,
                  event_record_id: int, entity_id: str = "") -> dict:
    """
    Full routing pipeline for one event.
    Returns result dict with status, target entity ID, and error if any.
    """
    from middleware.retry_handler import with_retry, RetryExhausted, is_retryable
    from event_logger import log_processing, log_success, log_failure
    import time

    start = time.monotonic()

    route = find_route(source, event_type)
    if not route:
        log.info("No route found for %s:%s — skipping", source, event_type)
        from event_logger import log_skipped
        log_skipped(event_record_id, f"No active route for {source}:{event_type}")
        return {"status": "skipped", "reason": "no_route"}

    log_processing(event_record_id, route_id=route["route_id"], transformer=route["transformer"])

    try:
        transformed = transform_payload(route, raw_payload, source, event_type)
    except Exception as exc:
        log.error("Transform failed for route %s: %s", route["route_id"], exc)
        log_failure(event_record_id, f"Transform error: {exc}", move_to_dlq=False)
        return {"status": "failed", "error": f"Transform error: {exc}"}

    try:
        result = with_retry(
            dispatch, route, transformed,
            event_id=f"EVT-{event_record_id}"
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log_success(
            event_record_id,
            target=route["target"],
            target_entity_id=str(result.get("recordId") or result.get("issueKey") or ""),
            processing_ms=elapsed_ms,
        )
        log.info("Event EVT-%s processed in %dms via route %s",
                 event_record_id, elapsed_ms, route["route_id"])
        return {"status": "success", **result}

    except RetryExhausted as exc:
        log.error("Event EVT-%s permanently failed after %d retries: %s",
                  event_record_id, exc.attempt_count, exc.last_error)
        log_failure(event_record_id,
                    error=f"{exc.last_error}",
                    retry_count=exc.attempt_count,
                    move_to_dlq=True)
        return {"status": "dead_letter", "error": str(exc.last_error)}

    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log_failure(event_record_id, str(exc))
        return {"status": "failed", "error": str(exc)}
