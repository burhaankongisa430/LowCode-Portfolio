"""
Microsoft Teams notifier.
Posts Adaptive Cards to Teams channels via incoming webhook URLs.
"""

import requests
from config import Config


class TeamsNotifier:

    @staticmethod
    def _post(webhook_url: str, payload: dict) -> bool:
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.ok
        except requests.RequestException:
            return False

    def post_new_ticket(self, ticket: dict) -> bool:
        """Posts a new ticket notification to the relevant team channel."""
        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "🎫 New Ticket",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Accent"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{ticket['ticketId']} — {ticket['title']}",
                            "wrap": True,
                            "weight": "Bolder"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Priority",  "value": ticket.get("priority", "")},
                                {"title": "Category",  "value": ticket.get("category", "")},
                                {"title": "Submitter", "value": ticket.get("submitterName", "")},
                                {"title": "SLA Due",   "value": str(ticket.get("dueDate", ""))},
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View Ticket",
                            "url": f"https://{Config.QB_REALM_HOSTNAME}/nav/app/{Config.QB_APP_ID}/action/record?rid={ticket['recordId']}"
                        }
                    ]
                }
            }]
        }
        return self._post(Config.TEAMS_WEBHOOK_URL, card)

    def post_sla_breach(self, ticket: dict) -> bool:
        """Posts a critical SLA breach card to the escalation channel."""
        hours_overdue = abs(ticket.get("timeRemainingHours", 0))
        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "Container",
                            "style": "attention",
                            "items": [{
                                "type": "TextBlock",
                                "text": "🚨 SLA BREACH",
                                "weight": "Bolder",
                                "size": "Large",
                                "color": "Attention"
                            }]
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{ticket['ticketId']} — {ticket['title']}",
                            "wrap": True,
                            "weight": "Bolder"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Priority",      "value": ticket.get("priority", "")},
                                {"title": "Hours Overdue", "value": f"{hours_overdue:.1f}h"},
                                {"title": "Agent",         "value": ticket.get("assignedAgent", "Unassigned")},
                                {"title": "Team",          "value": ticket.get("assignedTeam", "")},
                                {"title": "Submitter",     "value": ticket.get("submitterName", "")},
                                {"title": "SLA Due",       "value": str(ticket.get("dueDate", ""))},
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Resolve Now",
                            "url": f"https://{Config.QB_REALM_HOSTNAME}/nav/app/{Config.QB_APP_ID}/action/record?rid={ticket['recordId']}"
                        }
                    ]
                }
            }]
        }
        return self._post(Config.TEAMS_ESCALATION_WEBHOOK_URL, card)

    def post_at_risk_warning(self, ticket: dict) -> bool:
        """Posts an at-risk warning card."""
        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"⚠ SLA At Risk: {ticket['ticketId']}",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Warning"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Title",           "value": ticket.get("title", "")},
                                {"title": "Priority",        "value": ticket.get("priority", "")},
                                {"title": "Hours Remaining", "value": f"{ticket.get('timeRemainingHours', 0):.1f}h"},
                                {"title": "SLA Due",         "value": str(ticket.get("dueDate", ""))},
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Update Ticket",
                            "url": f"https://{Config.QB_REALM_HOSTNAME}/nav/app/{Config.QB_APP_ID}/action/record?rid={ticket['recordId']}"
                        }
                    ]
                }
            }]
        }
        return self._post(Config.TEAMS_WEBHOOK_URL, card)
