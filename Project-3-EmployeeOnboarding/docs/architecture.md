# Architecture & Data Model

## Quickbase Table Definitions

### Table 1: Employees (New Hires)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Employee ID | Formula (Text) | "EMP-" & ToText([Record ID#]) |
| 7 | First Name | Text | Required |
| 8 | Last Name | Text | Required |
| 9 | Full Name | Formula (Text) | [First Name] & " " & [Last Name] |
| 10 | Personal Email | Email | For pre-boarding comms before work email exists |
| 11 | Work Email | Email | Set after provisioning |
| 12 | Phone | Phone | |
| 13 | Job Title | Text | Required |
| 14 | Department | Record Link (Departments) | Required |
| 15 | Hiring Manager | Text | Manager name |
| 16 | Hiring Manager Email | Email | |
| 17 | Buddy | Text | Assigned buddy name |
| 18 | Buddy Email | Email | |
| 19 | Start Date | Date | Required |
| 20 | Employment Type | Text (multi-choice) | Permanent, Contract, Intern |
| 21 | Work Location | Text (multi-choice) | Office, Remote, Hybrid |
| 22 | Office Location | Text | City / Site |
| 23 | Onboarding Plan | Record Link (Onboarding Plans) | Assigned at creation |
| 24 | Onboarding Status | Text (multi-choice) | Pre-boarding, Active, Completed, On Hold |
| 25 | Overall Progress % | Formula (Numeric) | Summary-driven |
| 26 | Phase Progress % | Formula (Numeric) | Current phase only |
| 27 | Current Phase | Formula (Text) | Based on days since start |
| 28 | Days Until Start | Formula (Numeric) | |
| 29 | Days Since Start | Formula (Numeric) | |
| 30 | Total Tasks | Summary (Tasks) | Count of all tasks |
| 31 | Completed Tasks | Summary (Tasks) | Count where Status = Completed |
| 32 | Overdue Tasks | Summary (Tasks) | Count where Is Overdue = true |
| 33 | AD Account Created | Checkbox | Set by provisioner |
| 34 | M365 License Assigned | Checkbox | Set by provisioner |
| 35 | Equipment Ordered | Checkbox | Set when equipment task completed |
| 36 | Date Created | Date/Time | Auto |
| 37 | Notes | Text (multiline) | |
| 38 | Onboarding Health | Formula (Text) | On Track / At Risk / Delayed |

---

### Table 2: Departments

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Department Name | Text | Engineering, Sales, Finance, HR, Operations, Marketing |
| 7 | Department Head | Text | |
| 8 | Department Head Email | Email | |
| 9 | Default Onboarding Plan | Record Link (Onboarding Plans) | |
| 10 | Teams Channel Webhook | URL | For department notifications |
| 11 | IT Contact | Text | Who handles IT tasks for this dept |
| 12 | IT Contact Email | Email | |

---

### Table 3: Onboarding Plans (Templates)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Plan Name | Text | "Engineering – Permanent", "Sales – Remote", etc. |
| 7 | Role Category | Text (multi-choice) | Engineering, Sales, Finance, Operations, Marketing, HR |
| 8 | Employment Type | Text (multi-choice) | Permanent, Contract, Intern |
| 9 | Work Location | Text (multi-choice) | Office, Remote, Hybrid, All |
| 10 | Total Task Count | Summary (Task Templates) | |
| 11 | Description | Text (multiline) | What this plan covers |
| 12 | Is Active | Checkbox | |

---

### Table 4: Task Templates (Reference — per Plan)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Onboarding Plan | Record Link (Onboarding Plans) | |
| 7 | Task Name | Text | Required |
| 8 | Phase | Text (multi-choice) | Pre-boarding, Day 1, Week 1, Month 1, 90 Days |
| 9 | Owner Role | Text (multi-choice) | IT, HR, Manager, Buddy, New Hire, Facilities |
| 10 | Due Days Offset | Numeric | Days relative to start date (negative = before start) |
| 11 | Description | Text (multiline) | Instructions for the task owner |
| 12 | Is Blocking | Checkbox | If true, next phase cannot start until complete |
| 13 | Category | Text (multi-choice) | Access & Systems, Equipment, Compliance, Training, Social, Admin |
| 14 | Sort Order | Numeric | Display order within phase |

**Sample Task Templates — Engineering/Permanent:**

| Task Name | Phase | Owner | Due Offset | Category |
|-----------|-------|-------|-----------|----------|
| Order laptop and peripherals | Pre-boarding | IT | -10 | Equipment |
| Create Active Directory account | Pre-boarding | IT | -7 | Access & Systems |
| Assign M365 license & email | Pre-boarding | IT | -7 | Access & Systems |
| Add to Slack workspace | Pre-boarding | IT | -5 | Access & Systems |
| Add to GitHub organization | Pre-boarding | IT | -5 | Access & Systems |
| Send welcome email with Day 1 instructions | Pre-boarding | HR | -3 | Admin |
| Prepare desk / set up workstation | Pre-boarding | Facilities | -2 | Equipment |
| Complete employment contract | Pre-boarding | New Hire | -1 | Compliance |
| Collect ID for FICA/verification | Day 1 | HR | 0 | Compliance |
| Building access card issued | Day 1 | Facilities | 0 | Equipment |
| Meet with hiring manager | Day 1 | Manager | 0 | Social |
| IT orientation session | Day 1 | IT | 0 | Training |
| Meet the buddy | Day 1 | Buddy | 0 | Social |
| Complete payroll form | Day 1 | HR | 1 | Compliance |
| Complete personal details on HRIS | Week 1 | New Hire | 2 | Admin |
| Team introduction meeting | Week 1 | Manager | 2 | Social |
| Development environment setup | Week 1 | IT | 3 | Access & Systems |
| Security awareness training | Week 1 | HR | 5 | Training |
| Review team coding standards | Week 1 | Buddy | 5 | Training |
| 30-day check-in with manager | Month 1 | Manager | 30 | Admin |
| Complete compliance e-learning | Month 1 | New Hire | 21 | Compliance |
| 90-day probation review | 90 Days | Manager | 85 | Admin |

---

### Table 5: Onboarding Tasks (Generated per Hire)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Task ID | Formula (Text) | "TSK-" & ToText([Record ID#]) |
| 7 | Employee | Record Link (Employees) | |
| 8 | Task Name | Text | Copied from template |
| 9 | Phase | Text (multi-choice) | Pre-boarding, Day 1, Week 1, Month 1, 90 Days |
| 10 | Owner Role | Text (multi-choice) | IT, HR, Manager, Buddy, New Hire, Facilities |
| 11 | Owner Name | Text | Resolved at generation time |
| 12 | Owner Email | Email | Resolved at generation time |
| 13 | Status | Text (multi-choice) | Not Started, In Progress, Completed, Overdue, Blocked, N/A |
| 14 | Due Date | Date | Calculated from hire start date + offset |
| 15 | Completed Date | Date | Set when Status = Completed |
| 16 | Completed By | Text | Who completed it |
| 17 | Description | Text (multiline) | Instructions |
| 18 | Category | Text (multi-choice) | Access & Systems, Equipment, Compliance, Training, Social, Admin |
| 19 | Is Blocking | Checkbox | From template |
| 20 | Is Overdue | Formula (Checkbox) | Today() > Due Date and Status ≠ Completed |
| 21 | Days Until Due | Formula (Numeric) | |
| 22 | Days Overdue | Formula (Numeric) | |
| 23 | Sort Order | Numeric | |
| 24 | Notes | Text (multiline) | Completion notes |
| 25 | Date Created | Date/Time | Auto |

---

### Table 6: Equipment Requests

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Request ID | Formula (Text) | "EQR-" & ToText([Record ID#]) |
| 7 | Employee | Record Link (Employees) | |
| 8 | Equipment Type | Text (multi-choice) | Laptop, Monitor, Keyboard, Mouse, Headset, Docking Station, Phone, Other |
| 9 | Specification | Text | Model/spec details |
| 10 | Quantity | Numeric | |
| 11 | Status | Text (multi-choice) | Requested, Approved, Ordered, Delivered, Canceled |
| 12 | Requested By | Text | Manager name |
| 13 | Required By Date | Date | Must arrive before start date |
| 14 | Supplier | Text | |
| 15 | Order Reference | Text | PO or supplier ref |
| 16 | Estimated Cost | Numeric (currency) | |
| 17 | Delivery Notes | Text | |
| 18 | Date Created | Date/Time | Auto |

---

## Table Relationships

```
Departments (1) ─────────────── (many) Employees
Departments (1) ─────────────── (1)    Onboarding Plans [default]
Onboarding Plans (1) ─────────── (many) Task Templates
Onboarding Plans (1) ─────────── (many) Employees [assigned plan]
Employees (1) ───────────────── (many) Onboarding Tasks  [generated]
Employees (1) ───────────────── (many) Equipment Requests
Task Templates ─── (seed data — not linked at runtime, used for generation only)
```

---

## Role-Based Permissions

| Role | Employees | Tasks (own) | Tasks (all) | Equipment | Plans/Templates |
|------|-----------|-------------|-------------|-----------|-----------------|
| New Hire | View own | Edit own | None | View own | None |
| IT | View relevant | Edit IT tasks | None | Edit | None |
| HR | Full | Full | Full | Full | Full |
| Manager | View direct reports | Edit manager tasks | View team | View | None |
| Buddy | View assigned hire | Edit buddy tasks | None | None | None |
| HR Admin | Full | Full | Full | Full | Full |
