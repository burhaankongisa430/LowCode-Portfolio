# Quickbase Automations

---

## Automation 1: New Deal Created — Set Defaults & Notify Rep

**Trigger:** Record Created in **Deals** table  
**Condition:** None

### Actions:
1. **Update Record** (self)
   - Stage Changed Date: `Now()`
   - Previous Stage: `""`

2. **Send Email**
   - To: `[Sales Rep - Email]`
   - Subject: `"New Deal Assigned: " & [Deal ID] & " – " & [Deal Name]`
   - Body:
     ```
     Hi [Sales Rep - Rep Name],

     A new deal has been created and assigned to you.

     Deal ID:        [Deal ID]
     Deal Name:      [Deal Name]
     Company:        [Company - Company Name]
     Primary Contact:[Primary Contact - Full Name]
     Deal Value:     $[Deal Value]
     Stage:          [Stage]
     Expected Close: [Expected Close Date]
     Lead Source:    [Lead Source]

     Next step: Qualify this lead within 3 business days.

     View deal: [QB App Link]
     ```

3. **Send Webhook** to Power Automate lead intake flow (for Teams notification)

---

## Automation 2: Deal Stage Changed — Log & Notify

**Trigger:** Record Changed in **Deals** table  
**Condition:** `[Stage] != [Stage (previous value)]`

### Actions:
1. **Update Record** (self)
   - Stage Changed Date: `Now()`
   - Previous Stage: `[Stage (previous value)]`

2. **Create Record in Activities**
   - Deal: `[Record ID#]`
   - Activity Type: `"Stage Change"`
   - Subject: `"Stage changed from " & [Stage (previous value)] & " to " & [Stage]`
   - Activity Date: `Now()`
   - Logged By: `Current User`
   - Source: `"Automation"`

3. **Send Email** (conditional on forward progression)
   - To: `[Sales Rep - Email]`
   - Subject: `[Deal ID] & " advanced to " & [Stage]`
   - Body: Confirmation with next required actions

4. **Send Webhook** to Power Automate stage progression flow

---

## Automation 3: Deal Closed Won — Celebrate & Update

**Trigger:** Record Changed in **Deals** table  
**Condition:** `[Stage] = "Closed Won"` AND `[Stage (previous value)] != "Closed Won"`

### Actions:
1. **Update Record** (self)
   - Actual Close Date: `Today()`

2. **Send Email** to Sales Rep — congratulations notification

3. **Send Email** to Sales Manager — win notification with deal summary

4. **Create Record in Activities**
   - Activity Type: `"Stage Change"`
   - Subject: `"CLOSED WON: " & [Deal Name]`
   - Notes: `"Deal value: $" & ToText([Deal Value])`

5. **Send Webhook** to Power Automate won/lost notification flow

---

## Automation 4: Deal Closed Lost — Require Loss Reason

**Trigger:** Record Changed in **Deals** table  
**Condition:** `[Stage] = "Closed Lost"` AND `IsNull([Loss Reason])`

### Actions:
1. **Send Email**
   - To: `[Sales Rep - Email]`; CC: `[Sales Rep - Manager - Email]`
   - Subject: `"Action Required: Loss Reason Missing – " & [Deal ID]`
   - Body:
     ```
     Hi [Sales Rep - Rep Name],

     Deal [Deal ID] – "[Deal Name]" has been marked Closed Lost,
     but no loss reason was recorded.

     Please update the Loss Reason field within 24 hours.
     This data is critical for improving our sales process.

     Deal: [QB App Link]
     ```

2. **Create Record in Activities**
   - Activity Type: `"Note"`
   - Subject: `"CLOSED LOST – Loss reason required"`

---

## Automation 5: Daily Follow-up Digest (Scheduled)

**Trigger:** Scheduled — Daily at 07:30 SAST  
**Condition:** None (runs for all active reps)

### Logic:
1. **Send Webhook** to Power Automate follow-up reminder flow
   - Flow queries deals where:
     - `Follow-up Status = "Overdue"` OR `Follow-up Status = "Due Today"`
     - `Stage` NOT IN `("Closed Won", "Closed Lost")`
   - Groups by Sales Rep
   - Sends each rep a personalised digest of their overdue/due follow-ups

---

## Automation 6: Stalled Deal Alert (Scheduled)

**Trigger:** Scheduled — Every Monday at 08:00 SAST  
**Condition:** None

### Actions:
1. **Send Webhook** to Power Automate
   - Flow queries: `[Stalled Alert] = true` (no activity > 14 days, not closed)
   - Sends manager a grouped list of stalled deals by rep
   - Sends each rep their own stalled deal list

---

## Automation 7: Activity Logged — Update Deal Last Activity Date

**Trigger:** Record Created in **Activities** table  
**Condition:** NOT `IsNull([Deal])`

### Actions:
1. **Update Related Record in Deals**
   - Last Activity Date: `[Activity Date]` (from trigger record)

2. **Update Related Record in Contacts**
   - Last Activity Date: `[Activity Date]`

---

## Automation 8: Contact Assigned — Welcome Email

**Trigger:** Record Created in **Contacts** table  
**Condition:** `[Contact Type] = "Lead"`

### Actions:
1. **Send Email**
   - To: `[Owner - Email]` (Sales Rep)
   - Subject: `"New Lead: " & [Full Name] & " – " & [Company - Company Name]`
   - Body includes: contact details, lead source, lead score grade, suggested next action

---

## Pipeline: External Lead Intake

**Quickbase Pipeline** — triggered by webhook from Python API or website form

**Steps:**
1. **Trigger:** Webhook received at QB Pipeline URL
2. **Action:** Create record in Contacts table
3. **Action:** Create record in Deals table (linked to new Contact)
4. **Action:** Assign to next available rep (round-robin logic or territory)
5. **Action:** Log activity: "Lead created via {source}"
6. **Action:** Notify assigned rep

**Pipeline JSON reference:**
```json
{
  "name": "External Lead Intake",
  "steps": [
    {
      "type": "trigger",
      "source": "webhook",
      "outputSchema": {
        "firstName":   "string",
        "lastName":    "string",
        "email":       "string",
        "phone":       "string",
        "company":     "string",
        "jobTitle":    "string",
        "leadSource":  "string",
        "dealValue":   "number",
        "notes":       "string"
      }
    },
    {
      "type": "action",
      "app": "quickbase",
      "action": "createRecord",
      "table": "{{CONTACTS_TABLE_ID}}",
      "fields": {
        "First Name":    "{{trigger.firstName}}",
        "Last Name":     "{{trigger.lastName}}",
        "Email":         "{{trigger.email}}",
        "Phone":         "{{trigger.phone}}",
        "Job Title":     "{{trigger.jobTitle}}",
        "Contact Type":  "Lead",
        "Lead Source":   "{{trigger.leadSource}}"
      },
      "outputKey": "newContact"
    },
    {
      "type": "action",
      "app": "quickbase",
      "action": "createRecord",
      "table": "{{DEALS_TABLE_ID}}",
      "fields": {
        "Deal Name":         "{{trigger.firstName}} {{trigger.lastName}} – {{trigger.company}}",
        "Primary Contact":   "{{newContact.recordId}}",
        "Stage":             "New Lead",
        "Deal Value":        "{{trigger.dealValue}}",
        "Lead Source":       "{{trigger.leadSource}}",
        "Expected Close Date":"{{addDays(today(), 30)}}"
      }
    }
  ]
}
```
