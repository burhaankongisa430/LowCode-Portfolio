"""
Quickbase REST API v1 client — CRM & Sales Pipeline edition.
Covers Contacts, Companies, Deals, Activities, and Sales Reps tables.
"""

import requests
from datetime import datetime, timezone
from typing import Any
from config import Config


class QuickbaseError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class CRMQuickbaseClient:
    BASE_URL = "https://api.quickbase.com/v1"

    def __init__(self):
        self._headers = {
            "QB-Realm-Hostname": Config.QB_REALM_HOSTNAME,
            "Authorization":     f"QB-USER-TOKEN {Config.QB_USER_TOKEN}",
            "Content-Type":      "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        r = requests.request(method, url, headers=self._headers, timeout=15, **kwargs)
        if not r.ok:
            raise QuickbaseError(
                f"QB API {r.status_code}: {r.text[:200]}", status_code=r.status_code
            )
        return r.json()

    # ------------------------------------------------------------------ #
    #  Contacts                                                            #
    # ------------------------------------------------------------------ #

    def create_contact(self, first_name: str, last_name: str, email: str,
                       phone: str = "", job_title: str = "", contact_type: str = "Lead",
                       lead_source: str = "", lead_score: int = 0,
                       rep_record_id: int = None, notes: str = "") -> dict:
        data = {
            "7":  {"value": first_name},
            "8":  {"value": last_name},
            "10": {"value": email},
            "11": {"value": phone},
            "12": {"value": job_title},
            "15": {"value": contact_type},
            "16": {"value": lead_source},
            "17": {"value": lead_score},
            "25": {"value": notes},
        }
        if rep_record_id:
            data["19"] = {"value": rep_record_id}

        result = self._request("POST", "/records", json={
            "to": Config.QB_CONTACTS_TABLE,
            "data": [data],
            "fieldsToReturn": [3, 6, 9],
        })
        rec = result["data"][0]
        return {"recordId": rec["3"]["value"], "contactId": rec["6"]["value"]}

    def find_contact_by_email(self, email: str) -> dict | None:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_CONTACTS_TABLE,
            "select": [3, 6, 9, 10, 12, 14, 15, 17],
            "where": f"{{10.EX.'{email}'}}",
            "options": {"top": 1},
        })
        if not result["data"]:
            return None
        return self._map_contact(result["data"][0])

    def update_contact_lead_score(self, record_id: int, score: int) -> dict:
        return self._request("POST", "/records", json={
            "to": Config.QB_CONTACTS_TABLE,
            "data": [{"3": {"value": record_id}, "17": {"value": score}}],
        })

    # ------------------------------------------------------------------ #
    #  Deals                                                               #
    # ------------------------------------------------------------------ #

    def create_deal(self, deal_name: str, contact_record_id: int,
                    stage: str = "New Lead", deal_value: float = 0,
                    expected_close_date: str = "", lead_source: str = "",
                    rep_record_id: int = None, priority: str = "Medium",
                    company_record_id: int = None) -> dict:
        data = {
            "7":  {"value": deal_name},
            "8":  {"value": contact_record_id},
            "11": {"value": stage},
            "12": {"value": deal_value},
            "17": {"value": lead_source},
            "38": {"value": priority},
        }
        if expected_close_date:
            data["15"] = {"value": expected_close_date}
        if rep_record_id:
            data["10"] = {"value": rep_record_id}
        if company_record_id:
            data["9"] = {"value": company_record_id}

        result = self._request("POST", "/records", json={
            "to": Config.QB_DEALS_TABLE,
            "data": [data],
            "fieldsToReturn": [3, 6, 13, 14],
        })
        rec = result["data"][0]
        return {
            "recordId":      rec["3"]["value"],
            "dealId":        rec["6"]["value"],
            "winProb":       rec["13"]["value"],
            "weightedValue": rec["14"]["value"],
        }

    def update_deal_stage(self, record_id: int, new_stage: str, notes: str = "") -> dict:
        fields = {
            "3":  {"value": record_id},
            "11": {"value": new_stage},
        }
        if new_stage in ("Closed Won", "Closed Lost"):
            fields["16"] = {"value": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
        if notes:
            fields["30"] = {"value": notes}
        return self._request("POST", "/records", json={
            "to": Config.QB_DEALS_TABLE,
            "data": [fields],
        })

    def get_open_deals(self, rep_record_id: int = None) -> list[dict]:
        where = "{11.XEX.'Closed Won'} AND {11.XEX.'Closed Lost'}"
        if rep_record_id:
            where += f" AND {{10.EX.'{rep_record_id}'}}"
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_DEALS_TABLE,
            "select": [3, 6, 7, 9, 10, 11, 12, 13, 14, 21, 22, 23, 24, 25, 27, 31, 32],
            "where": where,
            "sortBy": [{"fieldId": 14, "order": "DESC"}],
            "options": {"top": 500},
        })
        return [self._map_deal(r) for r in result.get("data", [])]

    def get_stalled_deals(self) -> list[dict]:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_DEALS_TABLE,
            "select": [3, 6, 7, 9, 10, 11, 12, 23, 31, 32],
            "where": "{32.EX.'Stalled'} AND {11.XEX.'Closed Won'} AND {11.XEX.'Closed Lost'}",
            "sortBy": [{"fieldId": 23, "order": "DESC"}],
            "options": {"top": 200},
        })
        return [self._map_deal(r) for r in result.get("data", [])]

    # ------------------------------------------------------------------ #
    #  Activities                                                          #
    # ------------------------------------------------------------------ #

    def log_activity(self, deal_record_id: int, contact_record_id: int,
                     activity_type: str, subject: str, notes: str = "",
                     outcome: str = "Neutral", logged_by: str = "System",
                     logged_by_email: str = "system@yourcompany.com",
                     source: str = "Manual",
                     follow_up_date: str = None) -> dict:
        data = {
            "7":  {"value": deal_record_id},
            "8":  {"value": contact_record_id},
            "9":  {"value": activity_type},
            "10": {"value": subject},
            "11": {"value": notes},
            "12": {"value": datetime.now(timezone.utc).isoformat()},
            "14": {"value": outcome},
            "15": {"value": logged_by},
            "16": {"value": logged_by_email},
            "17": {"value": source},
        }
        if follow_up_date:
            data["19"] = {"value": follow_up_date}
            data["18"] = {"value": True}

        return self._request("POST", "/records", json={
            "to": Config.QB_ACTIVITIES_TABLE,
            "data": [data],
            "fieldsToReturn": [3, 6],
        })

    # ------------------------------------------------------------------ #
    #  Sales Reps                                                          #
    # ------------------------------------------------------------------ #

    def get_reps_by_pipeline_load(self, limit: int = 1) -> list[dict]:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_REPS_TABLE,
            "select": [3, 6, 7, 8, 10, 12],
            "where": "{11.EX.'true'}",
            "sortBy": [{"fieldId": 12, "order": "ASC"}],
            "options": {"top": limit},
        })
        return result.get("data", [])

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _map_contact(raw: dict) -> dict:
        def v(fid): return raw.get(str(fid), {}).get("value")
        return {
            "recordId":   v(3), "contactId": v(6),
            "fullName":   v(9), "email":     v(10),
            "jobTitle":   v(12),"company":   v(14),
            "type":       v(15),"leadScore": v(17),
        }

    @staticmethod
    def _map_deal(raw: dict) -> dict:
        def v(fid): return raw.get(str(fid), {}).get("value")
        return {
            "recordId":         v(3),  "dealId":            v(6),
            "dealName":         v(7),  "company":           v(9),
            "salesRep":         v(10), "stage":             v(11),
            "dealValue":        v(12), "winProbability":    v(13),
            "weightedValue":    v(14), "expectedClose":     v(15),
            "nextFollowUp":     v(21), "daysInStage":       v(22),
            "daysSinceActivity":v(23), "dealAgeDays":       v(24),
            "followUpStatus":   v(25), "isOverdue":         v(27),
            "dealHealthScore":  v(31), "dealHealthLabel":   v(32),
        }
