"""
Jira webhook payload transformer.
Converts Jira issue webhooks into normalized QB Service Desk format.

Jira sends webhooks for:
  - jira:issue_created  → create QB ticket
  - jira:issue_updated  → update QB ticket status/priority
  - jira:issue_deleted  → flag QB ticket as canceled
"""

import logging

log = logging.getLogger(__name__)


def _map_priority(jira_priority: str) -> str:
    mapping = {
        "Highest": "P1-Critical",
        "High":    "P2-High",
        "Medium":  "P3-Medium",
        "Low":     "P4-Low",
        "Lowest":  "P4-Low",
    }
    return mapping.get(jira_priority, "P3-Medium")


def _map_status(jira_status: str) -> str:
    mapping = {
        "To Do":       "New",
        "Open":        "New",
        "In Progress": "In Progress",
        "In Review":   "In Progress",
        "Done":        "Resolved",
        "Closed":      "Closed",
        "Canceled":   "Closed",
        "Won't Do":    "Closed",
    }
    return mapping.get(jira_status, "New")


def _extract_issue_fields(issue: dict) -> dict:
    """Extract commonly needed fields from a Jira issue object."""
    fields = issue.get("fields", {})
    return {
        "key":           issue.get("key", ""),
        "summary":       fields.get("summary", ""),
        "description":   (fields.get("description") or {}).get("content", [{}])[0].get("content", [{}])[0].get("text", ""),
        "priority":      (fields.get("priority") or {}).get("name", "Medium"),
        "status":        (fields.get("status") or {}).get("name", "Open"),
        "reporter_name": (fields.get("reporter") or {}).get("displayName", ""),
        "reporter_email":(fields.get("reporter") or {}).get("emailAddress", ""),
        "assignee_name": (fields.get("assignee") or {}).get("displayName", ""),
        "assignee_email":(fields.get("assignee") or {}).get("emailAddress", ""),
        "created":       fields.get("created", ""),
        "updated":       fields.get("updated", ""),
        "labels":        fields.get("labels", []),
        "project_key":   (fields.get("project") or {}).get("key", ""),
    }


def transform_issue_created(payload: dict) -> dict:
    issue  = payload.get("issue", {})
    f      = _extract_issue_fields(issue)
    labels = ", ".join(f["labels"])

    return {
        "source":          "Jira",
        "event_type":      "jira:issue_created",
        "source_entity_id": f["key"],
        "target_app":      "service_desk",
        "target_table":    "",  # resolved by router
        "action":          "create_record",
        "fields": {
            "7":  f["summary"],
            "8":  f["description"] or f"Synced from Jira {f['key']}",
            "9":  "IT-Software",          # default category for Jira issues
            "10": _map_priority(f["priority"]),
            "11": _map_status(f["status"]),
            "12": f["reporter_name"],
            "13": f["reporter_email"],
            "31": f"jira:{f['key']}" + (f", {labels}" if labels else ""),
        },
        "meta": {
            "jiraKey":     f["key"],
            "jiraProject": f["project_key"],
        }
    }


def transform_issue_updated(payload: dict) -> dict:
    issue      = payload.get("issue", {})
    changelog  = payload.get("changelog", {})
    f          = _extract_issue_fields(issue)
    changes    = {item["field"]: item for item in changelog.get("items", [])}

    qb_fields = {}
    if "status" in changes:
        qb_fields["11"] = _map_status(changes["status"].get("toString", ""))
    if "priority" in changes:
        qb_fields["10"] = _map_priority(changes["priority"].get("toString", ""))
    if "summary" in changes:
        qb_fields["7"] = changes["summary"].get("toString", "")
    if "assignee" in changes:
        qb_fields["14"] = changes["assignee"].get("toString", "")

    return {
        "source":          "Jira",
        "event_type":      "jira:issue_updated",
        "source_entity_id": f["key"],
        "action":          "update_record",
        "fields":          qb_fields,
        "lookup_key":      "jiraKey",
        "lookup_value":    f["key"],
    }


def transform_issue_resolved(payload: dict) -> dict:
    issue = payload.get("issue", {})
    f     = _extract_issue_fields(issue)

    return {
        "source":          "Jira",
        "event_type":      "jira:issue_resolved",
        "source_entity_id": f["key"],
        "action":          "update_record",
        "fields":          {"11": "Resolved"},
        "lookup_key":      "jiraKey",
        "lookup_value":    f["key"],
    }


def transform(payload: dict, event_type: str) -> dict:
    if event_type == "jira:issue_created":
        return transform_issue_created(payload)
    if event_type in ("jira:issue_updated",):
        return transform_issue_updated(payload)
    if event_type == "jira:issue_resolved":
        return transform_issue_resolved(payload)
    raise ValueError(f"Jira transformer: unsupported event_type '{event_type}'")
