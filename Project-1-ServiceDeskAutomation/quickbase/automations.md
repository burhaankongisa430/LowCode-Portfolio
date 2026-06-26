# Quickbase Automations

All automations are configured in the Quickbase App Builder under **Settings > Automations**.

---

## Automation 1: New Ticket — Set Initial Assignment

**Trigger:** Record Created in **Tickets** table  
**Condition:** `[Status] = "New"`

### Actions (in order):
1. **Send Email**
   - To: `[Submitter Email]`
   - Subject: `"Ticket Received: " & [Ticket ID] & " – " & [Title]`
   - Body:
     ```
     Hi [Submitter Name],

     Thank you for contacting the Service Desk.

     Your ticket has been received and assigned the reference: [Ticket ID]

     Priority: [Priority]
     Expected resolution by: [Due Date]

     You will receive updates as your ticket progresses.

     Service Desk Team
     ```

2. **Send Webhook (HTTP POST)**
   - URL: `https://your-power-automate-webhook-url/ticket-routing`
   - Payload:
     ```json
     {
       "ticketId": "{{[Record ID#]}}",
       "title": "{{[Title]}}",
       "category": "{{[Category]}}",
       "priority": "{{[Priority]}}",
       "routingTeam": "{{[Routing Team]}}",
       "submitterEmail": "{{[Submitter Email]}}",
       "submitterName": "{{[Submitter Name]}}",
       "dueDate": "{{[Due Date]}}",
       "createdDate": "{{[Date Created]}}"
     }
     ```

---

## Automation 2: Ticket Resolved — Notify Submitter & Log Resolution

**Trigger:** Record Changed in **Tickets** table  
**Condition:** `[Status] = "Resolved"` AND `[Status (previous value)] != "Resolved"`

### Actions:
1. **Send Email**
   - To: `[Submitter Email]`
   - Subject: `[Ticket ID] & " – Resolved"`
   - Body:
     ```
     Hi [Submitter Name],

     Your ticket [Ticket ID] – "[Title]" has been resolved.

     Resolution Time: [Resolution Time Hours] hours
     SLA Status: [SLA Status]

     Please rate your experience: [satisfaction survey link]

     If this issue recurs, please reply to this email.

     Service Desk Team
     ```

2. **Create Record in Audit Log**
   - Ticket: `[Record ID#]`
   - Action: `"Status Change"`
   - Old Value: `[Status (previous value)]`
   - New Value: `"Resolved"`
   - Performed By: `"System"`
   - Timestamp: `Now()`

---

## Automation 3: SLA Breach Alert

**Trigger:** Record Changed OR Scheduled (every 15 minutes)  
**Condition:** `[Is Overdue] = true` AND `[Status] != "Resolved"` AND `[Status] != "Closed"`

### Actions:
1. **Send Email**
   - To: `[Assigned Agent - Email]`; CC: Team Lead email
   - Subject: `"⚠ SLA BREACHED: " & [Ticket ID]`
   - Body:
     ```
     URGENT: SLA Breached

     Ticket: [Ticket ID] – [Title]
     Priority: [Priority]
     Submitter: [Submitter Name]
     Due Date: [Due Date]
     Current Status: [Status]

     Immediate action required.
     ```

2. **Send Webhook**
   - To Power Automate escalation flow
   - Payload includes ticket details and escalation level

---

## Automation 4: Status Changed — Audit Log Entry

**Trigger:** Record Changed in **Tickets** table  
**Condition:** `[Status] != [Status (previous value)]`

### Actions:
1. **Create Record in Audit Log**
   - Ticket: `[Record ID#]`
   - Action: `"Status Change"`
   - Old Value: `[Status (previous value)]`
   - New Value: `[Status]`
   - Performed By: `Current User`
   - Timestamp: `Now()`

---

## Automation 5: Agent Assignment Changed — Notify New Agent

**Trigger:** Record Changed in **Tickets** table  
**Condition:** `[Assigned Agent] changed` AND NOT `IsNull([Assigned Agent])`

### Actions:
1. **Send Email**
   - To: `[Assigned Agent - Email]`
   - Subject: `"New Ticket Assigned: " & [Ticket ID]`
   - Body:
     ```
     Hi [Assigned Agent - Agent Name],

     A ticket has been assigned to you.

     Ticket ID: [Ticket ID]
     Title: [Title]
     Priority: [Priority]
     Category: [Category]
     Submitter: [Submitter Name] ([Submitter Email])
     SLA Due: [Due Date]
     Current Status: [Status]

     Description:
     [Description]

     View ticket: [QB App URL]/db/[Table ID]?a=dr&rid=[Record ID#]

     Service Desk System
     ```

2. **Create Record in Audit Log**
   - Ticket: `[Record ID#]`
   - Action: `"Assignment"`
   - New Value: `[Assigned Agent - Agent Name]`
   - Performed By: `Current User`
   - Timestamp: `Now()`

---

## Automation 6: Ticket Closed — Archive After 30 Days

**Trigger:** Scheduled — Daily at 02:00  
**Condition:** `[Status] = "Resolved"` AND `DateDiff(Now(), [Resolution Date], "days") >= 30`

### Actions:
1. **Update Record**
   - Status: `"Closed"`

2. **Create Record in Audit Log**
   - Action: `"Auto-Closed"`
   - New Value: `"Closed"`
   - Performed By: `"System – Scheduled"`

---

## Automation 7: Daily SLA Summary to Managers

**Trigger:** Scheduled — Daily at 07:00  
**Condition:** None (runs always)

### Actions:
1. **Send Webhook** to Power Automate daily-summary flow
   - Flow queries QB API for:
     - Open P1/P2 tickets
     - Breached tickets count
     - Tickets due today
     - Agent workload summary

---

## Pipeline: Ticket Intake from External Systems

**Quickbase Pipeline** — triggered by incoming webhook from Python API

**Steps:**
1. Trigger: `Webhook received` at `https://api.quickbase.com/v1/pipelines/{pipelineId}/trigger`
2. Action: `Create Record` in Tickets table
   - Map JSON body fields to table fields
3. Action: `Create Record` in Audit Log
   - Action: `"Created via API"`
4. Action: `Send notification` via connected channel

**Pipeline JSON Reference:**
```json
{
  "name": "Intake from External Systems",
  "steps": [
    {
      "type": "trigger",
      "source": "webhook",
      "outputSchema": {
        "title": "string",
        "description": "string",
        "category": "string",
        "priority": "string",
        "submitter_name": "string",
        "submitter_email": "string"
      }
    },
    {
      "type": "action",
      "app": "quickbase",
      "action": "createRecord",
      "table": "{{TICKETS_TABLE_ID}}",
      "fields": {
        "Title":           "{{trigger.title}}",
        "Description":     "{{trigger.description}}",
        "Category":        "{{trigger.category}}",
        "Priority":        "{{trigger.priority}}",
        "Submitter Name":  "{{trigger.submitter_name}}",
        "Submitter Email": "{{trigger.submitter_email}}",
        "Status":          "New"
      }
    }
  ]
}
```
