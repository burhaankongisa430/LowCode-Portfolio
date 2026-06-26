# Quickbase Automations

---

## Automation 1: Event Failed — Move to Dead Letter Queue (After Max Retries)

**Trigger:** Record Changed in **Integration Events**  
**Condition:** `[Status] = "Dead Letter"` AND `[Status (previous value)] != "Dead Letter"`

### Actions:
1. **Create Record in Dead Letter Queue**
   - Event: `[Record ID#]`
   - Source System: `[Source System]`
   - Event Type: `[Event Type]`
   - Original Payload: `[Payload]`
   - Failure Reason: `[Error Message]`
   - Retry Count: `[Retry Count]`
   - First Failed At: `Now()`
   - Status: `"Pending"`

2. **Send Webhook** to Power Automate integration alert flow
   ```json
   {
     "eventId":      "{{[Event ID]}}",
     "source":       "{{[Source System]}}",
     "eventType":    "{{[Event Type]}}",
     "routeLabel":   "{{[Route Label]}}",
     "errorMessage": "{{[Error Message]}}",
     "retryCount":   {{[Retry Count]}}
   }
   ```

---

## Automation 2: Route Failure Rate Alert (Scheduled)

**Trigger:** Scheduled — Every 30 minutes  
**Condition:** Any Integration Route where `[Failure Rate Today] >= 20` AND `[Is Active] = true`

### Actions:
1. **Send Webhook** to Power Automate integration alert flow

---

## Automation 3: Dead Letter Queue — Daily Count Alert

**Trigger:** Scheduled — Daily at 08:00 SAST  
**Condition:** Count of DLQ records where `[Status] = "Pending"` > 5

### Actions:
1. **Send Email**
   - To: `integration-ops@yourcompany.com`
   - Subject: `"DLQ Alert: " & COUNT(pending DLQ items) & " events awaiting retry"`
   - Body: list of pending DLQ items grouped by source system

---

## Automation 4: Daily Health Aggregation (Scheduled)

**Trigger:** Scheduled — Daily at 23:55 SAST  
**Condition:** None

### Actions:
1. **Send Webhook** to Python handler `POST /api/integrations/aggregate-health`
   - Handler queries all today's events, groups by source, computes success rate
   - Creates one Health record per source system

---

## Automation 5: New Route Activated — Smoke Test

**Trigger:** Record Changed in **Integration Routes**  
**Condition:** `[Is Active] = true` AND `[Is Active (previous value)] = false`

### Actions:
1. **Send Webhook** to Python handler `POST /api/integrations/smoke-test`
   - Payload: `{ "routeId": "{{[Route ID]}}" }`
   - Handler sends a synthetic test event through the route to verify end-to-end connectivity
