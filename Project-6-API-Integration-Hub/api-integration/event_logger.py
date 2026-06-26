"""
Event logger — writes every integration event to the QB Integration Events table.
Called immediately on receipt (before processing) to guarantee no event is
silently lost, even if processing fails.

Also handles:
  - Deduplication key generation and lookup
  - Status updates throughout the event lifecycle
  - Dead Letter Queue record creation on permanent failure
"""

import hashlib
import json
import logging
import requests
from datetime import datetime, timezone
from config import Config

log = logging.getLogger(__name__)

_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _qb_post(body: dict) -> dict:
    r = requests.post("https://api.quickbase.com/v1/records",
                      headers=_HEADERS, json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def _qb_query(table: str, select: list, where: str) -> list:
    r = requests.post("https://api.quickbase.com/v1/records/query",
                      headers=_HEADERS,
                      json={"from": table, "select": select, "where": where, "options": {"top": 1}},
                      timeout=10)
    r.raise_for_status()
    return r.json().get("data", [])


def generate_dedup_key(source: str, event_type: str, entity_id: str) -> str:
    raw = f"{source}:{event_type}:{entity_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def is_duplicate(dedup_key: str) -> bool:
    """Check if this exact event was processed in the last DEDUP_WINDOW_SECONDS."""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=Config.DEDUP_WINDOW_SECONDS)).isoformat()
    rows = _qb_query(
        Config.QB_EVENTS_TABLE,
        select=[3],
        where=f"{{20.EX.'{dedup_key}'}} AND {{21.AF.'{cutoff}'}}",
    )
    return len(rows) > 0


def log_received(source: str, event_type: str, payload: dict,
                 entity_id: str = "", source_ip: str = "") -> int:
    """
    Write an event record immediately on receipt.
    Returns the QB record ID of the created event log entry.
    """
    dedup_key = generate_dedup_key(source, event_type, entity_id)
    payload_str = json.dumps(payload)[:10000]  # cap at 10k chars

    result = _qb_post({
        "to": Config.QB_EVENTS_TABLE,
        "data": [{
            "7":  {"value": source},
            "8":  {"value": event_type},
            "11": {"value": "Received"},
            "12": {"value": payload_str},
            "18": {"value": entity_id},
            "20": {"value": dedup_key},
            "21": {"value": datetime.now(timezone.utc).isoformat()},
            "24": {"value": source_ip},
        }],
        "fieldsToReturn": [3, 6],
    })

    record_id = result["data"][0]["3"]["value"]
    log.debug("Event logged: %s (QB record %s)", event_type, record_id)
    return record_id


def log_processing(record_id: int, route_id: str = "", transformer: str = "") -> None:
    _qb_post({"to": Config.QB_EVENTS_TABLE, "data": [{
        "3":  {"value": record_id},
        "11": {"value": "Processing"},
        "10": {"value": route_id},
        "23": {"value": transformer},
    }]})


def log_success(record_id: int, target: str, target_entity_id: str = "",
                response_body: str = "", processing_ms: int = 0) -> None:
    _qb_post({"to": Config.QB_EVENTS_TABLE, "data": [{
        "3":  {"value": record_id},
        "9":  {"value": target},
        "11": {"value": "Success"},
        "14": {"value": response_body[:2000]},
        "17": {"value": processing_ms},
        "19": {"value": target_entity_id},
        "22": {"value": datetime.now(timezone.utc).isoformat()},
    }]})


def log_failure(record_id: int, error: str, retry_count: int = 0,
                move_to_dlq: bool = False) -> None:
    new_status = "Dead Letter" if move_to_dlq else "Failed"
    _qb_post({"to": Config.QB_EVENTS_TABLE, "data": [{
        "3":  {"value": record_id},
        "11": {"value": new_status},
        "15": {"value": error[:2000]},
        "16": {"value": retry_count},
        "22": {"value": datetime.now(timezone.utc).isoformat()},
    }]})

    if move_to_dlq:
        _write_to_dlq(record_id, error, retry_count)


def log_skipped(record_id: int, reason: str = "duplicate") -> None:
    _qb_post({"to": Config.QB_EVENTS_TABLE, "data": [{
        "3":  {"value": record_id},
        "11": {"value": "Skipped"},
        "15": {"value": reason},
    }]})


def _write_to_dlq(event_record_id: int, failure_reason: str, retry_count: int) -> None:
    """Create a Dead Letter Queue entry for manual review and retry."""
    try:
        # Fetch the original event for its payload
        rows = _qb_query(Config.QB_EVENTS_TABLE, [7, 8, 12], f"{{3.EX.'{event_record_id}'}}")
        if not rows:
            return
        row = rows[0]
        _qb_post({"to": Config.QB_DLQ_TABLE, "data": [{
            "7":  {"value": row.get("7", {}).get("value", "")},
            "8":  {"value": row.get("8", {}).get("value", "")},
            "10": {"value": row.get("12", {}).get("value", "")},
            "11": {"value": failure_reason[:2000]},
            "12": {"value": retry_count},
            "13": {"value": datetime.now(timezone.utc).isoformat()},
            "15": {"value": "Pending"},
        }]})
        log.info("Event %d moved to Dead Letter Queue after %d retries",
                 event_record_id, retry_count)
    except Exception as exc:
        log.error("Failed to write DLQ record for event %d: %s", event_record_id, exc)
