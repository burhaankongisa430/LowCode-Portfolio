# Quickbase Automations

---

## Automation 1: New Employee Record Created — Trigger Task Generation

**Trigger:** Record Created in **Employees** table  
**Condition:** Not `IsNull([Start Date])` AND Not `IsNull([Department])`

### Actions:
1. **Send Webhook (HTTP POST)** to Python `webhook_handler.py`
   - URL: `https://your-api-server/api/onboarding/generate`
   - Payload:
     ```json
     {
       "employeeRecordId":   "{{[Record ID#]}}",
       "employeeId":         "{{[Employee ID]}}",
       "firstName":          "{{[First Name]}}",
       "lastName":           "{{[Last Name]}}",
       "personalEmail":      "{{[Personal Email]}}",
       "jobTitle":           "{{[Job Title]}}",
       "department":         "{{[Department - Department Name]}}",
       "departmentId":       "{{[Department - Record ID#]}}",
       "startDate":          "{{[Start Date]}}",
       "employmentType":     "{{[Employment Type]}}",
       "workLocation":       "{{[Work Location]}}",
       "managerName":        "{{[Hiring Manager]}}",
       "managerEmail":       "{{[Hiring Manager Email]}}",
       "buddyName":          "{{[Buddy]}}",
       "buddyEmail":         "{{[Buddy Email]}}",
       "onboardingPlanId":   "{{[Onboarding Plan - Record ID#]}}"
     }
     ```
   - The Python handler:
     1. Looks up Task Templates for the assigned Onboarding Plan
     2. Batch-creates all Onboarding Task records
     3. Triggers Azure AD provisioning flow
     4. Returns `{"tasksCreated": 34, "adProvisioned": true}`

2. **Send Webhook** to Power Automate kickoff flow (Teams + email notifications)

---

## Automation 2: Task Completed — Update Employee Progress

**Trigger:** Record Changed in **Onboarding Tasks** table  
**Condition:** `[Status] = "Completed"` AND `[Status (previous value)] != "Completed"`

### Actions:
1. **Update Record** (self)
   - Completed Date: `Today()`

2. **Send Webhook** to Power Automate task-completion flow
   - Payload includes task details, employee info, and phase
   - Flow checks if all Phase tasks are complete → triggers milestone notification

---

## Automation 3: Overdue Task Status Sync (Scheduled)

**Trigger:** Scheduled — Daily at 06:00 SAST  
**Condition:** None

### Logic:
- For all tasks where:
  - `[Is Overdue] = true`
  - `[Status] != "Overdue"` (not yet flagged)
- **Update Record** — Status: `"Overdue"`

This keeps the Status field accurate for filtering without relying solely on the formula field.

---

## Automation 4: Day 1 Morning Alert to Hiring Manager

**Trigger:** Scheduled — Daily at 07:00 SAST  
**Condition:** Any Employee where `[Start Date] = Today()` AND `[Onboarding Status] = "Pre-boarding"`

### Actions:
1. **Update Record in Employees**
   - Onboarding Status: `"Active"`

2. **Send Email**
   - To: `[Hiring Manager Email]`
   - Subject: `[Full Name] & " starts today! 🎉 Here is your Day 1 checklist"`
   - Body: list of all Day 1 tasks owned by Manager, with descriptions and links

3. **Send Email**
   - To: `[Buddy Email]`
   - Subject: `"Your new colleague " & [Full Name] & " starts today"`

4. **Send Webhook** to Power Automate milestone flow → posts welcome card to team Teams channel

---

## Automation 5: Equipment Request Created — Notify IT

**Trigger:** Record Created in **Equipment Requests** table  
**Condition:** None

### Actions:
1. **Send Email**
   - To: `[Employee - Department - IT Contact Email]`
   - CC: `[Requested By]` (manager)
   - Subject: `"Equipment Request: " & [Request ID] & " for " & [Employee - Full Name]`
   - Body includes item, specification, required-by date, hire start date

---

## Automation 6: Onboarding Complete — Celebrate & Archive

**Trigger:** Record Changed in **Employees** table  
**Condition:** `[Overall Progress %] >= 100` AND `[Onboarding Status] != "Completed"`

### Actions:
1. **Update Record** (self)
   - Onboarding Status: `"Completed"`

2. **Send Email**
   - To: `[Work Email]` (new hire)
   - CC: `[Hiring Manager Email]`
   - Subject: `"🎉 Onboarding Complete! Welcome to the team, " & [First Name]`

3. **Send Webhook** to Power Automate → post celebration Teams card to department channel

---

## Automation 7: Start Date Changed — Recalculate Task Dates

**Trigger:** Record Changed in **Employees** table  
**Condition:** `[Start Date] != [Start Date (previous value)]`

### Actions:
1. **Send Webhook** to Python handler
   - Endpoint: `PATCH /api/onboarding/{{[Record ID#]}}/recalculate-dates`
   - Payload: `{"newStartDate": "{{[Start Date]}}"}`
   - Handler reads all tasks for this employee and patches each `Due Date`
