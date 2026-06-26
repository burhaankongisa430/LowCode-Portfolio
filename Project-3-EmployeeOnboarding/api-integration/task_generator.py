"""
Template-driven onboarding task generation engine.

When a new employee record is created, this module:
  1. Loads all Task Templates linked to the employee's Onboarding Plan
  2. Calculates the due date for each task (hire start date + offset_days)
  3. Resolves the owner email from the hire record (manager, buddy, new hire)
  4. Batch-creates all tasks in Quickbase in a single POST request
  5. Returns a summary dict

Batching matters: a hire with 40 tasks created individually takes ~40s.
One batch POST takes ~1s.
"""

import logging
from datetime import datetime, timedelta, timezone
from config import Config

log = logging.getLogger(__name__)


def _resolve_owner_email(owner_role: str, hire: dict) -> str:
    """Map task owner role to the actual person's email for this hire."""
    fixed = Config.OWNER_ROLE_EMAIL_MAP.get(owner_role)
    if fixed is not None:
        return fixed
    if owner_role == "Manager":
        return hire.get("managerEmail", "")
    if owner_role == "Buddy":
        return hire.get("buddyEmail", "")
    if owner_role == "New Hire":
        return hire.get("personalEmail", "")
    return ""


def _resolve_owner_name(owner_role: str, hire: dict) -> str:
    """Map task owner role to a display name."""
    if owner_role == "Manager":
        return hire.get("managerName", "Manager")
    if owner_role == "Buddy":
        return hire.get("buddyName", "Buddy")
    if owner_role == "New Hire":
        return f"{hire.get('firstName', '')} {hire.get('lastName', '')}".strip()
    if owner_role == "IT":
        return "IT Provisioning Team"
    if owner_role == "HR":
        return "HR Team"
    if owner_role == "Facilities":
        return "Facilities Team"
    return owner_role


def _calculate_due_date(start_date_str: str, offset_days: int) -> str:
    """
    Calculate absolute due date from hire start date + offset in days.
    Negative offset = before start date (pre-boarding tasks).
    Returns ISO date string: "YYYY-MM-DD"
    """
    start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    due = start + timedelta(days=offset_days)
    return due.isoformat()


def generate_tasks(hire: dict, templates: list[dict], qb_client) -> dict:
    """
    Main entry point. Creates all onboarding tasks for a hire from templates.

    Args:
        hire: dict with keys: employeeRecordId, firstName, lastName, personalEmail,
              startDate, managerName, managerEmail, buddyName, buddyEmail
        templates: list of task template dicts from QB (field-mapped by qb_client)
        qb_client: OnboardingQuickbaseClient instance

    Returns:
        {"tasksCreated": int, "errors": list}
    """
    if not templates:
        log.warning("No templates found for hire %s — no tasks generated.",
                    hire.get("employeeId", "unknown"))
        return {"tasksCreated": 0, "errors": ["No task templates found for this onboarding plan."]}

    task_records = []
    errors = []

    for template in templates:
        try:
            due_date = _calculate_due_date(
                hire["startDate"],
                int(template.get("dueDaysOffset", 0))
            )
            owner_role = template.get("ownerRole", "HR")

            task_records.append({
                "7":  {"value": hire["employeeRecordId"]},
                "8":  {"value": template.get("taskName", "Unnamed Task")},
                "9":  {"value": template.get("phase", "Week 1")},
                "10": {"value": owner_role},
                "11": {"value": _resolve_owner_name(owner_role, hire)},
                "12": {"value": _resolve_owner_email(owner_role, hire)},
                "13": {"value": "Not Started"},
                "14": {"value": due_date},
                "17": {"value": template.get("description", "")},
                "18": {"value": template.get("category", "Admin")},
                "19": {"value": template.get("isBlocking", False)},
                "23": {"value": int(template.get("sortOrder", 99))},
            })
        except Exception as exc:
            log.error("Failed to build task record for template '%s': %s",
                      template.get("taskName", "?"), exc)
            errors.append(str(exc))

    if not task_records:
        return {"tasksCreated": 0, "errors": errors or ["No task records built."]}

    # Batch-create all tasks in a single API call
    try:
        result = qb_client.batch_create_tasks(task_records)
        created_count = len(result.get("data", []))
        log.info("Created %d onboarding tasks for employee %s",
                 created_count, hire.get("employeeId"))
        return {"tasksCreated": created_count, "errors": errors}

    except Exception as exc:
        log.error("Batch task creation failed: %s", exc)
        errors.append(f"Batch creation error: {exc}")
        return {"tasksCreated": 0, "errors": errors}


def recalculate_task_dates(employee_record_id: int, new_start_date: str, qb_client) -> dict:
    """
    Called when a hire's start date changes.
    Reads all tasks for the hire, recalculates due dates, and patches them.
    """
    tasks = qb_client.get_tasks_by_employee(employee_record_id)
    if not tasks:
        return {"updated": 0, "message": "No tasks found for this employee."}

    patches = []
    for task in tasks:
        if task.get("status") in ("Completed", "N/A"):
            continue

        # Derive original offset from how far the original due date was from start
        # We stored the template offset in the task description context, but here
        # we recalculate using days from the new start date.
        # Since we don't store the offset on the task, we use the phase to re-estimate.
        phase_default_offsets = {
            "Pre-boarding": -5,
            "Day 1":        0,
            "Week 1":       3,
            "Month 1":      15,
            "90 Days":      60,
        }
        offset = phase_default_offsets.get(task.get("phase", "Week 1"), 0)
        new_due = _calculate_due_date(new_start_date, offset)

        patches.append({
            "3":  {"value": task["recordId"]},
            "14": {"value": new_due},
        })

    if not patches:
        return {"updated": 0, "message": "No open tasks to update."}

    qb_client.batch_update_tasks(patches)
    log.info("Recalculated %d task due dates for employee record %d", len(patches), employee_record_id)
    return {"updated": len(patches), "newStartDate": new_start_date}
