"""
Quickbase REST API v1 client — Employee Onboarding edition.
"""

import requests
from config import Config


class QuickbaseError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class OnboardingQuickbaseClient:
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
            raise QuickbaseError(f"QB {r.status_code}: {r.text[:200]}", status_code=r.status_code)
        return r.json()

    # ------------------------------------------------------------------ #
    #  Employees                                                           #
    # ------------------------------------------------------------------ #

    def get_employee(self, record_id: int) -> dict | None:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_EMPLOYEES_TABLE,
            "select": list(range(3, 39)),
            "where": f"{{3.EX.'{record_id}'}}",
            "options": {"top": 1},
        })
        if not result["data"]:
            return None
        return self._map_employee(result["data"][0])

    def update_employee(self, record_id: int, fields: dict) -> dict:
        payload = {str(k): {"value": v} for k, v in fields.items()}
        payload["3"] = {"value": record_id}
        return self._request("POST", "/records", json={
            "to": Config.QB_EMPLOYEES_TABLE,
            "data": [payload],
        })

    def get_employees_starting_today(self) -> list[dict]:
        from datetime import date
        today = date.today().isoformat()
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_EMPLOYEES_TABLE,
            "select": [3, 6, 9, 11, 13, 15, 16, 17, 18, 19, 24, 33],
            "where": f"{{19.EX.'{today}'}} AND {{24.EX.'Pre-boarding'}}",
        })
        return [self._map_employee(r) for r in result.get("data", [])]

    # ------------------------------------------------------------------ #
    #  Tasks                                                               #
    # ------------------------------------------------------------------ #

    def batch_create_tasks(self, task_records: list[dict]) -> dict:
        """Create up to 100 task records in one POST. Split into batches if needed."""
        batch_size = 100
        all_created = []
        for i in range(0, len(task_records), batch_size):
            batch = task_records[i:i + batch_size]
            result = self._request("POST", "/records", json={
                "to": Config.QB_TASKS_TABLE,
                "data": batch,
                "fieldsToReturn": [3, 6],
            })
            all_created.extend(result.get("data", []))
        return {"data": all_created}

    def batch_update_tasks(self, patches: list[dict]) -> dict:
        return self._request("POST", "/records", json={
            "to": Config.QB_TASKS_TABLE,
            "data": patches,
        })

    def get_tasks_by_employee(self, employee_record_id: int) -> list[dict]:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_TASKS_TABLE,
            "select": [3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23],
            "where": f"{{7.EX.'{employee_record_id}'}}",
            "sortBy": [{"fieldId": 9, "order": "ASC"}, {"fieldId": 23, "order": "ASC"}],
            "options": {"top": 500},
        })
        return [self._map_task(r) for r in result.get("data", [])]

    def get_overdue_tasks(self) -> list[dict]:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_TASKS_TABLE,
            "select": [3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 22],
            "where": "{20.EX.'true'} AND {13.XEX.'Completed'} AND {13.XEX.'N/A'}",
            "sortBy": [{"fieldId": 22, "order": "DESC"}],
            "options": {"top": 500},
        })
        return [self._map_task(r) for r in result.get("data", [])]

    def complete_task(self, record_id: int, completed_by: str) -> dict:
        return self._request("POST", "/records", json={
            "to": Config.QB_TASKS_TABLE,
            "data": [{
                "3":  {"value": record_id},
                "13": {"value": "Completed"},
                "15": {"value": ""},  # completed date set by formula/field
                "16": {"value": completed_by},
            }],
        })

    # ------------------------------------------------------------------ #
    #  Task Templates                                                      #
    # ------------------------------------------------------------------ #

    def get_templates_by_plan(self, plan_record_id: int) -> list[dict]:
        result = self._request("POST", "/records/query", json={
            "from": Config.QB_TASK_TEMPLATES_TABLE,
            "select": [3, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "where": f"{{6.EX.'{plan_record_id}'}}",
            "sortBy": [{"fieldId": 8, "order": "ASC"}, {"fieldId": 14, "order": "ASC"}],
            "options": {"top": 200},
        })
        return [self._map_template(r) for r in result.get("data", [])]

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _map_employee(raw: dict) -> dict:
        def v(fid): return raw.get(str(fid), {}).get("value")
        return {
            "recordId":          v(3),  "employeeId":     v(6),
            "firstName":         v(7),  "lastName":       v(8),
            "fullName":          v(9),  "personalEmail":  v(10),
            "workEmail":         v(11), "jobTitle":       v(13),
            "department":        v(14), "managerName":    v(15),
            "managerEmail":      v(16), "buddyName":      v(17),
            "buddyEmail":        v(18), "startDate":      v(19),
            "employmentType":    v(20), "workLocation":   v(21),
            "onboardingPlanId":  v(23), "onboardingStatus": v(24),
            "overallProgress":   v(25), "currentPhase":   v(27),
            "totalTasks":        v(30), "completedTasks": v(31),
            "overdueTasks":      v(32), "adAccountCreated": v(33),
        }

    @staticmethod
    def _map_task(raw: dict) -> dict:
        def v(fid): return raw.get(str(fid), {}).get("value")
        return {
            "recordId":    v(3),  "taskId":      v(6),
            "employee":    v(7),  "taskName":    v(8),
            "phase":       v(9),  "ownerRole":   v(10),
            "ownerName":   v(11), "ownerEmail":  v(12),
            "status":      v(13), "dueDate":     v(14),
            "completedDate": v(15),"completedBy": v(16),
            "category":    v(18), "isBlocking":  v(19),
            "isOverdue":   v(20), "daysUntilDue":v(21),
            "daysOverdue": v(22), "sortOrder":   v(23),
        }

    @staticmethod
    def _map_template(raw: dict) -> dict:
        def v(fid): return raw.get(str(fid), {}).get("value")
        return {
            "recordId":     v(3),  "planId":       v(6),
            "taskName":     v(7),  "phase":        v(8),
            "ownerRole":    v(9),  "dueDaysOffset":v(10),
            "description":  v(11), "isBlocking":   v(12),
            "category":     v(13), "sortOrder":    v(14),
        }
