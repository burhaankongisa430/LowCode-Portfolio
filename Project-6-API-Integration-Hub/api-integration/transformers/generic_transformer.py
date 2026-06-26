"""
Generic JSON-path field mapping transformer.

Maps fields from any source JSON to any target schema using a
declarative mapping configuration — no custom code required.

Field mapping config format:
  {
    "field_mappings": [
      { "source_path": "firstName",    "target_field": "7",  "type": "string" },
      { "source_path": "email",        "target_field": "10", "type": "email" },
      { "source_path": "amount",       "target_field": "16", "type": "number" },
      { "source_path": "$.nested.key", "target_field": "22", "type": "string" },
      { "source_path": "createdAt",    "target_field": "23", "type": "datetime" }
    ],
    "static_fields": [
      { "target_field": "19", "value": "New" }
    ]
  }

source_path supports:
  - "fieldName"           → root-level key
  - "parent.child"        → dot-notation nested key
  - "$.parent.child"      → JSONPath-style (same as dot-notation here)
  - "array[0].fieldName"  → first element of an array

type conversions supported: string, number, integer, boolean, email, datetime, date
"""

import logging
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)


def _get_by_path(data: dict, path: str) -> Any:
    """
    Extract a value from a nested dict using dot-notation or JSONPath-style paths.
    Returns None if the path does not exist.
    """
    # Strip leading $. if present
    path = path.lstrip("$").lstrip(".")
    parts = path.replace("[", ".").replace("]", "").split(".")
    current = data
    for part in parts:
        if part == "":
            continue
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (IndexError, ValueError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _coerce(value: Any, target_type: str) -> Any:
    """Convert a value to the specified type."""
    if value is None:
        return None
    if target_type == "string" or target_type == "email":
        return str(value).strip()
    if target_type == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    if target_type == "integer":
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0
    if target_type == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes")
    if target_type in ("datetime", "date"):
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        return str(value)
    return value


def transform(source_payload: dict, mapping_config: dict) -> dict:
    """
    Apply a mapping config to a source payload and return the transformed dict
    in Quickbase field format: { "field_id": value, ... }

    Also used for non-QB targets when the mapping config includes target-specific keys.
    """
    result = {}
    errors = []

    for mapping in mapping_config.get("field_mappings", []):
        source_path  = mapping.get("source_path", "")
        target_field = mapping.get("target_field", "")
        target_type  = mapping.get("type", "string")

        if not source_path or not target_field:
            continue

        raw_value = _get_by_path(source_payload, source_path)

        if raw_value is None and mapping.get("required"):
            errors.append(f"Required field '{source_path}' not found in source payload.")
            continue

        if raw_value is not None:
            try:
                result[target_field] = _coerce(raw_value, target_type)
            except Exception as exc:
                log.warning("Field mapping error '%s' → '%s': %s", source_path, target_field, exc)
                errors.append(str(exc))

    for static in mapping_config.get("static_fields", []):
        target_field = static.get("target_field", "")
        value        = static.get("value")
        if target_field:
            result[target_field] = value

    if errors:
        log.warning("Transform completed with %d error(s): %s", len(errors), errors)

    return result
