"""
Quickbase REST API v1 client — Procurement Approval System edition.
"""

import requests
from datetime import datetime, timezone
from config import Config


class QuickbaseError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class ProcurementQBClient:
    BASE_URL = "https://api.quickbase.com/v1"

    def __init__(self):
        self._h = {
            "QB-Realm-Hostname": Config.QB_REALM_HOSTNAME,
            "Authorization":     f"QB-USER-TOKEN {Config.QB_USER_TOKEN}",
            "Content-Type":      "application/json",
        }

    def _req(self, method: str, path: str, **kw) -> dict:
        r = requests.request(method, f"{self.BASE_URL}/{path.lstrip('/')}", headers=self._h, timeout=15, **kw)
        if not r.ok:
            raise QuickbaseError(f"QB {r.status_code}: {r.text[:200]}", r.status_code)
        return r.json()

    # ------------------------------------------------------------------ #
    #  Purchase Requests                                                   #
    # ------------------------------------------------------------------ #

    def update_request(self, record_id: int, fields: dict) -> dict:
        payload = {str(k): {"value": v} for k, v in fields.items()}
        payload["3"] = {"value": record_id}
        return self._req("POST", "/records", json={"to": Config.QB_REQUESTS_TABLE, "data": [payload]})

    def get_request(self, record_id: int) -> dict | None:
        result = self._req("POST", "/records/query", json={
            "from": Config.QB_REQUESTS_TABLE,
            "select": list(range(3, 45)),
            "where": f"{{3.EX.'{record_id}'}}",
            "options": {"top": 1},
        })
        if not result["data"]:
            return None
        return self._map_request(result["data"][0])

    def get_pending_requests(self) -> list[dict]:
        result = self._req("POST", "/records/query", json={
            "from": Config.QB_REQUESTS_TABLE,
            "select": [3, 6, 7, 9, 10, 16, 19, 21, 23, 25, 26, 27, 36, 43],
            "where": "{19.CT.'Pending'}",
            "sortBy": [{"fieldId": 43, "order": "ASC"}],
            "options": {"top": 500},
        })
        return [self._map_request(r) for r in result.get("data", [])]

    def get_sla_breached_requests(self) -> list[dict]:
        result = self._req("POST", "/records/query", json={
            "from": Config.QB_REQUESTS_TABLE,
            "select": [3, 6, 7, 9, 10, 16, 19, 21, 23, 25, 26, 27, 36],
            "where": "{43.EX.'true'} AND {19.CT.'Pending'}",
            "options": {"top": 200},
        })
        return [self._map_request(r) for r in result.get("data", [])]

    # ------------------------------------------------------------------ #
    #  Purchase Orders                                                     #
    # ------------------------------------------------------------------ #

    def create_po_record(self, request_record_id: int, po_data: dict, html: str) -> dict:
        result = self._req("POST", "/records", json={
            "to": Config.QB_PO_TABLE,
            "data": [{
                "7":  {"value": request_record_id},
                "9":  {"value": po_data.get("requestorName", "")},
                "10": {"value": po_data.get("department", "")},
                "11": {"value": po_data.get("budgetCode", "")},
                "12": {"value": float(po_data.get("totalAmount", 0))},
                "13": {"value": po_data.get("currency", "ZAR")},
                "14": {"value": po_data.get("paymentTerms", "Net 30")},
                "15": {"value": po_data.get("deliveryAddress", "")},
                "16": {"value": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
                "18": {"value": "Issued"},
                "24": {"value": html},
            }],
            "fieldsToReturn": [3, 6],
        })
        rec = result["data"][0]
        return {"recordId": rec["3"]["value"], "poNumber": rec["6"]["value"]}

    def update_po_erp_reference(self, po_record_id: int, erp_ref: str) -> dict:
        return self._req("POST", "/records", json={
            "to": Config.QB_PO_TABLE,
            "data": [{"3": {"value": po_record_id}, "23": {"value": erp_ref}}],
        })

    # ------------------------------------------------------------------ #
    #  Approval History                                                    #
    # ------------------------------------------------------------------ #

    def log_approval_event(self, request_record_id: int, level: int, approver_name: str,
                           approver_email: str, decision: str, comments: str = "",
                           sent_date: str = None) -> dict:
        data = {
            "6":  {"value": request_record_id},
            "7":  {"value": level},
            "8":  {"value": approver_name},
            "9":  {"value": approver_email},
            "10": {"value": decision},
            "11": {"value": comments},
            "12": {"value": datetime.now(timezone.utc).isoformat()},
            "15": {"value": "Email"},
        }
        if sent_date:
            data["14"] = {"value": sent_date}
        return self._req("POST", "/records", json={"to": Config.QB_APPROVAL_HIST_TABLE, "data": [data]})

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _map_request(raw: dict) -> dict:
        def v(fid): return raw.get(str(fid), {}).get("value")
        return {
            "recordId":           v(3),  "requestNumber":  v(6),
            "title":              v(7),  "requestorName":  v(9),
            "requestorEmail":     v(10), "totalAmount":    v(16),
            "status":             v(19), "currentLevel":   v(21),
            "managerEmail":       v(23), "deptHeadEmail":  v(25),
            "financeDirectorEmail":v(26),"ceoEmail":       v(27),
            "isUrgent":           v(36), "slaBreached":    v(43),
        }
