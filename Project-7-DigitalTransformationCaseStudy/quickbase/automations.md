# Quickbase Automations — Transformation Tracker

---

## Automation 1: Milestone Completed — Update Initiative Progress

**Trigger:** Record Changed in **Milestones** table  
**Condition:** `[Status] = "Complete"` AND `[Status (previous value)] != "Complete"`

### Actions:
1. **Update Record** — set `[Actual Date]` = `Today()`
2. **Send Webhook** to Power Automate milestone completion flow
3. **Create Record in Activity Log**
   - Initiative: linked
   - Action: `"Milestone Completed: " & [Milestone Name]`
   - Date: `Now()`

---

## Automation 2: Monthly ROI Snapshot — Scheduled

**Trigger:** Scheduled — 1st of each month at 06:00 SAST  
**Condition:** None

### Actions:
1. **Send Webhook** to Python handler `POST /api/transformation/snapshot`
   - Handler queries all ROI measurement records
   - Computes YTD actuals vs projections
   - Creates a monthly ROI Snapshot record in QB
   - Triggers the Power Automate monthly report flow

---

## Automation 3: Benefit Realization Below Target — Alert

**Trigger:** Record Changed in **ROI Measurements** table  
**Condition:** `[Realization Status] = "Underperforming"` AND `[Realization Status (previous value)] != "Underperforming"`

### Actions:
1. **Send Email**
   - To: `transformation-lead@yourcompany.com`; CC: `[Initiative Owner Email]`
   - Subject: `[Initiative Name] — Benefit realization at " & ToText([Benefit Realization %]) & "% (target: 85%)"`
   - Body: metric breakdown, gap analysis, recommended actions

2. **Send Webhook** to Power Automate benefit realization alert flow

---

## Automation 4: Initiative Delay Alert — Scheduled

**Trigger:** Scheduled — Every Monday at 08:00 SAST  
**Condition:** Any Initiative where `[Schedule Status] = "Overdue"` AND `[Completion %] < 100`

### Actions:
1. **Send Email**
   - To: `[Initiative Owner Email]`; CC: `transformation-lead@yourcompany.com`
   - Subject: `"Schedule Alert: " & [Initiative Name] & " is " & ToText([Schedule Variance Days]) & " day(s) overdue"`

---

## Automation 5: Stakeholder Update — Scheduled

**Trigger:** Scheduled — Every 2 weeks (1st and 15th) at 07:00 SAST  
**Condition:** None

### Actions:
1. **Send Webhook** to Power Automate stakeholder update flow
   - Flow aggregates all initiative statuses
   - Generates a concise HTML summary
   - Sends to the stakeholder distribution list
