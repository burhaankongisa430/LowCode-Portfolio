# Quickbase Automations — Executive Dashboard

---

## Automation 1: Health Score Critical — Immediate Alert

**Trigger:** Record Created in **KPI Snapshots** table  
**Condition:** `[Health Score] < 55` (Critical threshold)

### Actions:
1. **Send Webhook** to Power Automate KPI alert flow
   ```json
   {
     "snapshotId":       "{{[Snapshot ID]}}",
     "snapshotTime":     "{{[Snapshot Time]}}",
     "healthScore":      {{[Health Score]}},
     "healthStatus":     "{{[Health Status]}}",
     "weakestDomain":    "{{[Weakest Domain]}}",
     "operationalScore": {{[Operational Score]}},
     "commercialScore":  {{[Commercial Score]}},
     "peopleScore":      {{[People Score]}},
     "financeScore":     {{[Finance Score]}},
     "alertSeverity":    "Critical"
   }
   ```

---

## Automation 2: Health Score Warning — Batch Alert

**Trigger:** Scheduled — Daily at 08:00 SAST  
**Condition:** Latest snapshot `[Health Score]` < 70 AND >= 55

### Actions:
1. **Send Webhook** to Power Automate alert flow with `alertSeverity: "Warning"`

---

## Automation 3: Weekly Snapshot Summary — Trigger Report Flow

**Trigger:** Scheduled — Monday at 06:30 SAST  
**Condition:** None

### Actions:
1. **Send Webhook** to Power Automate executive report flow
   - Payload: latest snapshot record + 7-day trend averages

---

## Automation 4: ETL Failure — Source System Unavailable

**Trigger:** Record Created in **KPI Snapshots** table  
**Condition:** `[Domains Available] < 4`

### Actions:
1. **Send Email**
   - To: `etl-ops@yourcompany.com`
   - Subject: `"ETL Warning: Only " & ToText([Domains Available]) & " of 4 domains available"`
   - Body: includes `[ETL Errors]` JSON field showing which sources failed

---

## Automation 5: Monthly KPI Archive (Storage Management)

**Trigger:** Scheduled — 1st of each month at 03:00 SAST  
**Condition:** Snapshot records older than 90 days

### Actions:
1. **Send Webhook** to Python handler `POST /api/kpi/archive`
   - Handler aggregates hourly snapshots into daily records
   - Deletes source hourly records older than 90 days
   - Reduces table size by ~95% for records > 90 days old
