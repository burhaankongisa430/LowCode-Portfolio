"""
Microsoft Teams connector — posts notifications and Adaptive Cards.
Used as a secondary target for high-priority events (e.g., employee terminations).
"""

import logging
import requests
from config import Config

log = logging.getLogger(__name__)


def send(payload: dict) -> dict:
    """
    Post a message or Adaptive Card to a Teams channel.

    payload keys:
      - webhook_url:  Teams incoming webhook URL (defaults to Config.TEAMS_WEBHOOK_URL)
      - message:      Plain text message (simple notification)
      - card:         Adaptive Card JSON body (if provided, overrides message)
      - title:        Card title
      - facts:        list of {"title": str, "value": str} dicts
    """
    webhook_url = payload.get("webhook_url") or Config.TEAMS_WEBHOOK_URL
    if not webhook_url:
        raise ValueError("Teams webhook URL is not configured.")

    if payload.get("card"):
        body = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": payload["card"]
            }]
        }
    else:
        body = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {"type": "TextBlock", "text": payload.get("title", "Integration Hub"), "weight": "Bolder", "size": "Medium"},
                        {"type": "FactSet", "facts": payload.get("facts", [])},
                        {"type": "TextBlock", "text": payload.get("message", ""), "wrap": True, "isSubtle": True}
                    ]
                }
            }]
        }

    r = requests.post(webhook_url, json=body, timeout=10)
    r.raise_for_status()
    log.info("Teams notification sent: %s", payload.get("title", ""))
    return {"status": "success", "channel": webhook_url[:40] + "..."}
