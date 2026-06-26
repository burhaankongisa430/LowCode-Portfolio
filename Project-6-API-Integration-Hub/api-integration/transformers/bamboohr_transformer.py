"""
BambooHR webhook payload transformer.
Converts BambooHR webhook events into the normalized format
expected by the Quickbase EmployeeOnboarding app.

BambooHR sends webhooks for:
  - employee.created   → trigger onboarding record creation
  - employee.updated   → sync profile changes to QB
  - employee.terminated → offboarding trigger + Teams notification
"""

import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)


def _map_employment_status(bhr_status: str) -> str:
    mapping = {
        "Active":      "Active",
        "Inactive":    "Pre-boarding",
        "Terminated":  "Completed",
        "On Leave":    "On Hold",
    }
    return mapping.get(bhr_status, "Pre-boarding")


def _map_employment_type(bhr_type: str) -> str:
    if not bhr_type:
        return "Permanent"
    lower = bhr_type.lower()
    if "contract" in lower:
        return "Contract"
    if "intern" in lower or "temp" in lower:
        return "Intern"
    return "Permanent"


def transform_employee_created(payload: dict) -> dict:
    """
    Map a BambooHR employee.created webhook to the QB Employees table format.

    BambooHR webhook payload structure:
    {
      "employeeId": "123",
      "fields": {
        "firstName": "Jane",
        "lastName": "Smith",
        "workEmail": "jane.smith@company.com",
        "personalEmail": "jane@gmail.com",
        "jobTitle": "Software Engineer",
        "department": "Engineering",
        "location": "Cape Town",
        "employeeType": "Regular Full-Time",
        "hireDate": "2026-08-01",
        "supervisorEId": "45",
        "supervisor": "John Manager"
      }
    }
    """
    fields = payload.get("fields", payload)
    employee_id = payload.get("employeeId", "") or payload.get("id", "")

    return {
        "source":          "BambooHR",
        "event_type":      "employee.created",
        "source_entity_id":str(employee_id),
        "target_app":      "onboarding",
        "target_table":    "",  # resolved by router from route config
        "action":          "create_record",
        "fields": {
            "7":  fields.get("firstName", ""),
            "8":  fields.get("lastName", ""),
            "10": fields.get("personalEmail") or fields.get("workEmail", ""),
            "11": fields.get("workEmail", ""),
            "13": fields.get("jobTitle", ""),
            "15": fields.get("supervisor", ""),
            "19": fields.get("hireDate", ""),
            "20": _map_employment_type(fields.get("employeeType", "")),
            "21": fields.get("location", "Office"),
            "24": _map_employment_status(fields.get("employmentHistoryStatus", "Inactive")),
        },
        "meta": {
            "bamboohrEmployeeId": str(employee_id),
            "hireDate":           fields.get("hireDate", ""),
            "department":         fields.get("department", ""),
        }
    }


def transform_employee_updated(payload: dict) -> dict:
    """Map employee.updated to a QB record update."""
    fields      = payload.get("fields", payload)
    employee_id = payload.get("employeeId", "")
    changed     = payload.get("changedFields", list(fields.keys()))

    qb_fields = {}
    field_map = {
        "firstName":  "7",  "lastName":   "8",
        "personalEmail": "10", "workEmail": "11",
        "jobTitle":   "13", "supervisor": "15",
    }
    for bhr_field, qb_fid in field_map.items():
        if bhr_field in changed and bhr_field in fields:
            qb_fields[qb_fid] = fields[bhr_field]

    return {
        "source":          "BambooHR",
        "event_type":      "employee.updated",
        "source_entity_id":str(employee_id),
        "action":          "update_record",
        "fields":          qb_fields,
        "lookup_key":      "bamboohrEmployeeId",
        "lookup_value":    str(employee_id),
    }


def transform_employee_terminated(payload: dict) -> dict:
    """Map employee.terminated — updates QB + sends Teams notification."""
    fields      = payload.get("fields", payload)
    employee_id = payload.get("employeeId", "")

    return {
        "source":          "BambooHR",
        "event_type":      "employee.terminated",
        "source_entity_id":str(employee_id),
        "action":          "multi_target",
        "targets": [
            {
                "target": "quickbase",
                "target_app": "onboarding",
                "action": "update_record",
                "lookup_key": "bamboohrEmployeeId",
                "lookup_value": str(employee_id),
                "fields": {
                    "24": "Completed",
                }
            },
            {
                "target": "teams",
                "title": "Employee Terminated",
                "facts": [
                    {"title": "Name",        "value": f"{fields.get('firstName')} {fields.get('lastName')}"},
                    {"title": "Employee ID", "value": str(employee_id)},
                    {"title": "End Date",    "value": fields.get("terminationDate", "—")},
                    {"title": "Reason",      "value": fields.get("terminationReason", "Not specified")},
                ],
                "message": "IT: Revoke access. HR: Process final pay. Manager: Knowledge transfer."
            }
        ]
    }


def transform(payload: dict, event_type: str) -> dict:
    """Dispatcher — routes to the correct transform function by event type."""
    if event_type == "employee.created":
        return transform_employee_created(payload)
    if event_type == "employee.updated":
        return transform_employee_updated(payload)
    if event_type == "employee.terminated":
        return transform_employee_terminated(payload)
    raise ValueError(f"BambooHR transformer: unsupported event_type '{event_type}'")
