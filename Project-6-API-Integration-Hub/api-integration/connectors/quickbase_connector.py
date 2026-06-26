"""
Quickbase connector — delivers transformed payloads to any QB app.
Supports create_record, update_record, and delete_record actions.
Uses a per-target-app token so the hub can write to all 4 QB apps.
"""

import logging
import requests
from config import Config

log = logging.getLogger(__name__)

_BASE = "https://api.quickbase.com/v1"

# Token registry — maps target app identifier to QB user token
_TOKENS = {
    "service_desk": Config.QB_SD_TOKEN  or Config.QB_TOKEN,
    "crm":          Config.QB_CRM_TOKEN or Config.QB_TOKEN,
    "onboarding":   Config.QB_OB_TOKEN  or Config.QB_TOKEN,
    "hub":          Config.QB_TOKEN,
}


def _headers(app: str) -> dict:
    token = _TOKENS.get(app, Config.QB_TOKEN)
    return {
        "QB-Realm-Hostname": Config.QB_REALM,
        "Authorization":     f"QB-USER-TOKEN {token}",
        "Content-Type":      "application/json",
    }


def send(payload: dict) -> dict:
    """
    Deliver a payload to Quickbase.

    payload must contain:
      - target_app:    "service_desk" | "crm" | "onboarding" | "hub"
      - target_table:  QB table ID
      - action:        "create_record" | "update_record" | "delete_record"
      - fields:        dict of {field_id_str: value}
      - record_id:     required for update/delete
    """
    app    = payload.get("target_app", "hub")
    table  = payload.get("target_table", "")
    action = payload.get("action", "create_record")
    fields = payload.get("fields", {})

    if not table:
        raise ValueError("target_table is required for Quickbase connector")

    field_data = {str(k): {"value": v} for k, v in fields.items()}

    if action == "create_record":
        body = {"to": table, "data": [field_data], "fieldsToReturn": [3, 6]}
        r = requests.post(f"{_BASE}/records", headers=_headers(app), json=body, timeout=15)
        r.raise_for_status()
        result = r.json()
        created = result["data"][0] if result.get("data") else {}
        log.info("QB create_record → table %s | record %s", table, created.get("3", {}).get("value"))
        return {"status": "success", "recordId": created.get("3", {}).get("value")}

    if action == "update_record":
        record_id = payload.get("record_id")
        if not record_id:
            raise ValueError("record_id is required for update_record")
        field_data["3"] = {"value": record_id}
        r = requests.post(f"{_BASE}/records", headers=_headers(app),
                          json={"to": table, "data": [field_data]}, timeout=15)
        r.raise_for_status()
        log.info("QB update_record → table %s record %s", table, record_id)
        return {"status": "success", "recordId": record_id}

    if action == "delete_record":
        record_id = payload.get("record_id")
        r = requests.delete(f"{_BASE}/records", headers=_headers(app),
                            json={"from": table, "where": f"{{3.EX.'{record_id}}}"}, timeout=15)
        r.raise_for_status()
        return {"status": "success", "deleted": record_id}

    raise ValueError(f"Unknown action: {action}")
