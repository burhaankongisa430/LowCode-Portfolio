# Architecture & Data Model

## Quickbase Table Definitions

### Table 1: Tickets (Core Table)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Ticket ID | Formula (Text) | "TKT-" & ToText([Record ID#]) |
| 7 | Title | Text | Required |
| 8 | Description | Text (multiline) | Required |
| 9 | Category | Text (multi-choice) | IT-Hardware, IT-Software, IT-Network, HR-Leave, HR-Payroll, HR-Benefits, Finance-Invoice, Finance-Expense, Facilities |
| 10 | Priority | Text (multi-choice) | P1-Critical, P2-High, P3-Medium, P4-Low |
| 11 | Status | Text (multi-choice) | New, Assigned, In Progress, Pending, Resolved, Closed |
| 12 | Submitter Name | Text | Required |
| 13 | Submitter Email | Email | Required |
| 14 | Assigned Agent | Record Link (Agents) | |
| 15 | Assigned Team | Text | Auto-populated via formula |
| 16 | Date Created | Date/Time | Auto (creation timestamp) |
| 17 | Date Modified | Date/Time | Auto |
| 18 | Due Date | Formula (Date/Time) | SLA-driven calculation |
| 19 | First Response Date | Date/Time | Manual/automated |
| 20 | Resolution Date | Date/Time | Set when Status = Resolved |
| 21 | Resolution Time Hours | Formula (Numeric) | DateDiff formula |
| 22 | SLA Status | Formula (Text) | On Track / At Risk / Breached / Met |
| 23 | Time Remaining Hours | Formula (Numeric) | Hours until SLA breach |
| 24 | SLA Color | Formula (Text) | Hex color code for UI |
| 25 | Routing Team | Formula (Text) | Category → Team mapping |
| 26 | Response SLA Hours | Formula (Numeric) | Priority → hours |
| 27 | Resolution SLA Hours | Formula (Numeric) | Priority → hours |
| 28 | First Response Due | Formula (Date/Time) | Created + Response SLA |
| 29 | Is Overdue | Formula (Checkbox) | Boolean |
| 30 | Ticket Age Days | Formula (Numeric) | |
| 31 | Tags | Text | Comma-separated |
| 32 | Attachments | File Attachment | |
| 33 | Internal Notes | Text (multiline) | Agent-only field |
| 34 | Customer Satisfaction | Numeric | 1-5 rating |

---

### Table 2: Agents

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Agent Name | Text | Required |
| 7 | Email | Email | Required |
| 8 | Team | Text (multi-choice) | IT Support, HR, Finance, Facilities |
| 9 | Specialization | Text | Comma-separated skills |
| 10 | Max Capacity | Numeric | Default: 10 |
| 11 | Is Active | Checkbox | |
| 12 | Active Ticket Count | Report Link (Summary) | Count of open tickets |
| 13 | Workload Status | Formula (Text) | Available / Near Capacity / At Capacity |
| 14 | Capacity Percentage | Formula (Numeric) | (Active / Max) * 100 |
| 15 | Last Assigned | Date/Time | Auto-updated |

---

### Table 3: Teams

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Team Name | Text | IT Support, HR, Finance, Facilities |
| 7 | Department | Text | |
| 8 | Team Lead | Record Link (Agents) | |
| 9 | Categories Handled | Text | Comma-separated |
| 10 | Email Distribution | Email | Team inbox |
| 11 | Teams Channel Webhook | URL | MS Teams webhook URL |
| 12 | Active Agents Count | Report Link (Summary) | |
| 13 | Open Tickets Count | Report Link (Summary) | |

---

### Table 4: SLA Policies

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Priority | Text | P1-Critical, P2-High, P3-Medium, P4-Low |
| 7 | Response Time Hours | Numeric | |
| 8 | Resolution Time Hours | Numeric | |
| 9 | Escalation L1 Hours | Numeric | Notify team lead |
| 10 | Escalation L2 Hours | Numeric | Notify manager |
| 11 | Business Hours Only | Checkbox | |

---

### Table 5: Knowledge Base

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Article ID | Formula (Text) | "KB-" & ToText([Record ID#]) |
| 7 | Title | Text | Required |
| 8 | Content | Rich Text | Full article body |
| 9 | Category | Text (multi-choice) | Matches ticket categories |
| 10 | Tags | Text | |
| 11 | View Count | Numeric | |
| 12 | Helpful Votes | Numeric | |
| 13 | Not Helpful Votes | Numeric | |
| 14 | Helpfulness Rate | Formula (Numeric) | % positive |
| 15 | Last Reviewed | Date | |
| 16 | Reviewed By | Text | |
| 17 | Is Published | Checkbox | |

---

### Table 6: Audit Log

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Ticket | Record Link (Tickets) | |
| 7 | Action | Text | Status Change, Assignment, Comment, etc. |
| 8 | Old Value | Text | |
| 9 | New Value | Text | |
| 10 | Performed By | Text | User name or "System" |
| 11 | Performed By Email | Email | |
| 12 | Timestamp | Date/Time | Auto |
| 13 | Notes | Text | |

---

## Table Relationships

```
Teams (1) ──────────────── (many) Agents
Teams (1) ──────────────── (many) Tickets  [via Routing Team]
Agents (1) ─────────────── (many) Tickets  [via Assigned Agent]
Tickets (1) ────────────── (many) Audit Log
SLA Policies (1) ────────── (many) Tickets [via Priority — formula lookup]
Knowledge Base ──── (independent, searched at intake)
```

---

## Role-Based Permissions

| Role | Tickets Access | Agents Table | SLA Table | Knowledge Base | Audit Log |
|------|---------------|-------------|-----------|---------------|-----------|
| End User | Create + View own | None | None | View published | None |
| Agent | View + Edit assigned | View self | View | View + Vote | View own actions |
| Team Lead | View + Edit team | View team | View | Full | View team |
| Manager | Full | Full | Full | Full | Full |
| Admin | Full | Full | Full | Full | Full |
