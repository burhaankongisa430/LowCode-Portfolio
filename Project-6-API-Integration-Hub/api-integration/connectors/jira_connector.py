"""
Jira REST API v3 connector.
Used both as a target (creating/updating issues) and as a source enricher
(fetching additional issue data when Jira sends a lightweight webhook).
"""

import logging
import requests
from base64 import b64encode
from config import Config

log = logging.getLogger(__name__)
_BASE = f"{Config.JIRA_BASE_URL}/rest/api/3"


def _auth() -> tuple[str, str]:
    return (Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)


def _headers() -> dict:
    creds = b64encode(f"{Config.JIRA_EMAIL}:{Config.JIRA_API_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def get_issue(issue_key: str) -> dict:
    """Fetch a Jira issue by key (e.g., 'SD-42')."""
    r = requests.get(f"{_BASE}/issue/{issue_key}", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def create_issue(project_key: str, summary: str, description: str,
                 issue_type: str = "Task", priority: str = "Medium",
                 labels: list[str] = None) -> dict:
    body = {
        "fields": {
            "project":     {"key": project_key},
            "summary":     summary,
            "description": {
                "type":    "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            },
            "issuetype": {"name": issue_type},
            "priority":  {"name": priority},
            "labels":    labels or [],
        }
    }
    r = requests.post(f"{_BASE}/issue", headers=_headers(), json=body, timeout=15)
    r.raise_for_status()
    result = r.json()
    log.info("Jira create_issue → %s", result.get("key"))
    return {"status": "success", "issueKey": result.get("key"), "id": result.get("id")}


def update_issue(issue_key: str, fields: dict) -> dict:
    r = requests.put(f"{_BASE}/issue/{issue_key}", headers=_headers(),
                     json={"fields": fields}, timeout=15)
    r.raise_for_status()
    log.info("Jira update_issue → %s", issue_key)
    return {"status": "success", "issueKey": issue_key}


def transition_issue(issue_key: str, transition_name: str) -> dict:
    """Move a Jira issue to a new status by transition name."""
    transitions_r = requests.get(
        f"{_BASE}/issue/{issue_key}/transitions",
        headers=_headers(), timeout=10
    )
    transitions_r.raise_for_status()
    transitions = transitions_r.json().get("transitions", [])
    match = next((t for t in transitions if t["name"].lower() == transition_name.lower()), None)
    if not match:
        raise ValueError(f"Transition '{transition_name}' not found for {issue_key}")

    r = requests.post(
        f"{_BASE}/issue/{issue_key}/transitions",
        headers=_headers(),
        json={"transition": {"id": match["id"]}},
        timeout=15,
    )
    r.raise_for_status()
    log.info("Jira transition_issue → %s to '%s'", issue_key, transition_name)
    return {"status": "success", "issueKey": issue_key, "transition": transition_name}


def send(payload: dict) -> dict:
    action = payload.get("action", "")

    if action == "create_issue":
        return create_issue(
            project_key=payload.get("project_key", Config.JIRA_SD_PROJECT),
            summary=payload.get("summary", ""),
            description=payload.get("description", ""),
            issue_type=payload.get("issue_type", "Task"),
            priority=payload.get("priority", "Medium"),
            labels=payload.get("labels", []),
        )
    if action == "update_issue":
        return update_issue(payload["issue_key"], payload.get("fields", {}))

    if action == "transition_issue":
        return transition_issue(payload["issue_key"], payload["transition"])

    raise ValueError(f"Jira connector: unsupported action '{action}'")
