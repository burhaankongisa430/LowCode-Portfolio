"""
Quickbase REST API v1 client.
Wraps records, queries, and table operations used by the service desk platform.
"""

import requests
from datetime import datetime, timezone
from typing import Any
from config import Config


class QuickbaseError(Exception):
    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class QuickbaseClient:
    BASE_URL = "https://api.quickbase.com/v1"

    def __init__(self):
        self._headers = {
            "QB-Realm-Hostname": Config.QB_REALM_HOSTNAME,
            "Authorization": f"QB-USER-TOKEN {Config.QB_USER_TOKEN}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        response = requests.request(method, url, headers=self._headers, timeout=15, **kwargs)
        if not response.ok:
            raise QuickbaseError(
                f"QB API error: {response.status_code} {response.text[:200]}",
                status_code=response.status_code,
                response_body=response.json() if response.content else None,
            )
        return response.json()

    # ------------------------------------------------------------------ #
    #  Tickets                                                             #
    # ------------------------------------------------------------------ #

    def create_ticket(self, title: str, description: str, category: str,
                      priority: str, submitter_name: str, submitter_email: str,
                      tags: str = "") -> dict:
        """Create a new ticket record and return {recordId, ticketId, dueDate}."""
        data = {
            "to": Config.QB_TICKETS_TABLE_ID,
            "data": [{
                "7":  {"value": title},
                "8":  {"value": description},
                "9":  {"value": category},
                "10": {"value": priority},
                "11": {"value": "New"},
                "12": {"value": submitter_name},
                "13": {"value": submitter_email},
                "31": {"value": tags},
            }],
            "fieldsToReturn": [3, 6, 18],
        }
        result = self._request("POST", "/records", json=data)
        record = result["data"][0]
        return {
            "recordId": record["3"]["value"],
            "ticketId": record["6"]["value"],
            "dueDate":  record["18"]["value"],
        }

    def update_ticket(self, record_id: int, fields: dict[int, Any]) -> dict:
        """Update specific fields on a ticket by record ID."""
        field_payload = {str(fid): {"value": val} for fid, val in fields.items()}
        field_payload["3"] = {"value": record_id}
        data = {
            "to": Config.QB_TICKETS_TABLE_ID,
            "data": [field_payload],
        }
        return self._request("POST", "/records", json=data)

    def get_ticket(self, record_id: int) -> dict:
        """Fetch a single ticket by record ID."""
        result = self.query_tickets(
            where=f"{{3.EX.'{record_id}'}}",
            select=[3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 29],
        )
        if not result["data"]:
            return None
        return self._map_ticket_record(result["data"][0])

    def query_tickets(self, where: str = "", select: list[int] = None,
                      sort_by: list[dict] = None, top: int = 100) -> dict:
        """Query tickets with an optional Quickbase query string."""
        payload = {
            "from": Config.QB_TICKETS_TABLE_ID,
            "select": select or [3, 6, 7, 10, 11, 12, 15, 18, 22, 23],
            "options": {"top": top},
        }
        if where:
            payload["where"] = where
        if sort_by:
            payload["sortBy"] = sort_by
        return self._request("POST", "/records/query", json=payload)

    def get_open_tickets(self) -> list[dict]:
        """Return all non-resolved/non-closed tickets."""
        result = self.query_tickets(
            where="{11.XEX.'Resolved'} AND {11.XEX.'Closed'}",
            select=[3, 6, 7, 10, 11, 12, 13, 14, 15, 16, 18, 22, 23, 29, 34],
            sort_by=[{"fieldId": 10, "order": "ASC"}, {"fieldId": 23, "order": "ASC"}],
            top=500,
        )
        return [self._map_ticket_record(r) for r in result.get("data", [])]

    def resolve_ticket(self, record_id: int) -> dict:
        return self.update_ticket(record_id, {
            11: "Resolved",
            20: datetime.now(timezone.utc).isoformat(),
        })

    # ------------------------------------------------------------------ #
    #  Agents                                                              #
    # ------------------------------------------------------------------ #

    def get_available_agents(self, team: str) -> list[dict]:
        """Return active agents in the given team who are not at capacity."""
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_AGENTS_TABLE_ID,
            "select": [3, 6, 7, 8, 10, 12, 13],
            "where": f"{{8.EX.'{team}'}} AND {{11.EX.'true'}} AND {{13.XEX.'At Capacity'}}",
            "sortBy": [{"fieldId": 12, "order": "ASC"}],
            "options": {"top": 20},
        })
        return result.get("data", [])

    def get_best_available_agent(self, team: str) -> dict | None:
        """Return the agent with the lowest current workload in the team."""
        agents = self.get_available_agents(team)
        return agents[0] if agents else None

    # ------------------------------------------------------------------ #
    #  Audit Log                                                           #
    # ------------------------------------------------------------------ #

    def log_audit_event(self, ticket_record_id: int, action: str,
                        old_value: str = "", new_value: str = "",
                        performed_by: str = "System",
                        performed_by_email: str = "system@yourcompany.com") -> dict:
        data = {
            "to": Config.QB_AUDIT_TABLE_ID,
            "data": [{
                "6":  {"value": ticket_record_id},
                "7":  {"value": action},
                "8":  {"value": old_value},
                "9":  {"value": new_value},
                "10": {"value": performed_by},
                "11": {"value": performed_by_email},
            }],
        }
        return self._request("POST", "/records", json=data)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _map_ticket_record(raw: dict) -> dict:
        """Flatten a QB record dict (field-id keyed) into named keys."""
        def v(field_id: int):
            return raw.get(str(field_id), {}).get("value")

        return {
            "recordId":          v(3),
            "ticketId":          v(6),
            "title":             v(7),
            "description":       v(8),
            "category":          v(9),
            "priority":          v(10),
            "status":            v(11),
            "submitterName":     v(12),
            "submitterEmail":    v(13),
            "assignedAgent":     v(14),
            "assignedTeam":      v(15),
            "dateCreated":       v(16),
            "dueDate":           v(18),
            "firstResponseDate": v(19),
            "resolutionDate":    v(20),
            "resolutionHours":   v(21),
            "slaStatus":         v(22),
            "timeRemainingHours":v(23),
            "isOverdue":         v(29),
            "escalationLevel":   v(34),
        }
