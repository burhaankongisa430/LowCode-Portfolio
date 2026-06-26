# Architecture & Data Model

## Quickbase Table Definitions

### Table 1: Integration Events (Core Audit Log)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Event ID | Formula (Text) | "EVT-" & Right("00000" & ToText([Record ID#]), 6) |
| 7 | Source System | Text (multi-choice) | BambooHR, Jira, Salesforce, Web Form, Quickbase, Manual |
| 8 | Event Type | Text | e.g., employee.created, issue.updated |
| 9 | Target System | Text (multi-choice) | Quickbase, Jira, BambooHR, Teams, ERP |
| 10 | Route ID | Text | Which routing rule handled this |
| 11 | Status | Text (multi-choice) | Received, Processing, Success, Failed, Dead Letter, Skipped |
| 12 | Payload | Text (multiline) | Raw inbound JSON (truncated to 10k chars) |
| 13 | Transformed Payload | Text (multiline) | Post-transformation JSON |
| 14 | Response Body | Text (multiline) | Target system response |
| 15 | Error Message | Text (multiline) | Error detail if failed |
| 16 | Retry Count | Numeric | 0 = first attempt |
| 17 | Processing Time ms | Numeric | End-to-end duration |
| 18 | Source Entity ID | Text | ID of the entity in the source system |
| 19 | Target Entity ID | Text | ID created/updated in the target system |
| 20 | Dedup Key | Text | SHA256 hash of source+type+entity ID |
| 21 | Date Created | Date/Time | Auto — time event was received |
| 22 | Date Processed | Date/Time | Time processing completed |
| 23 | Transformer Used | Text | Which transformer module was applied |
| 24 | IP Address | Text | Source IP of the webhook request |

---

### Table 2: Integration Routes (Routing Configuration)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Route ID | Formula (Text) | "R" & Right("00" & ToText([Record ID#]), 2) |
| 7 | Route Name | Text | Human-readable name |
| 8 | Source System | Text (multi-choice) | |
| 9 | Event Type | Text | Exact match e.g. "employee.created" or wildcard "*" |
| 10 | Target System | Text (multi-choice) | |
| 11 | Target Action | Text | e.g., "create_record", "update_record", "send_notification" |
| 12 | Target Table | Text | QB table ID, Jira project key, etc. |
| 13 | Transformer | Text | Module name: "bamboohr_transformer", "generic_transformer" |
| 14 | Mapping Config | Text (multiline) | JSON field mapping used by generic_transformer |
| 15 | Is Active | Checkbox | Toggle routes without deleting |
| 16 | Priority | Numeric | Lower = higher priority (1 runs first) |
| 17 | Max Retries | Numeric | Default 3 |
| 18 | Timeout Seconds | Numeric | Default 15 |
| 19 | Created By | Text | |
| 20 | Date Created | Date/Time | Auto |
| 21 | Event Count Today | Summary (Events) | Events processed today on this route |
| 22 | Success Count Today | Summary (Events) | Successful events today |
| 23 | Failure Count Today | Summary (Events) | Failed events today |

---

### Table 3: Dead Letter Queue

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | DLQ ID | Formula (Text) | "DLQ-" & ToText([Record ID#]) |
| 7 | Event | Record Link (Integration Events) | |
| 8 | Source System | Text | |
| 9 | Event Type | Text | |
| 10 | Original Payload | Text (multiline) | |
| 11 | Failure Reason | Text (multiline) | |
| 12 | Retry Count | Numeric | |
| 13 | First Failed At | Date/Time | |
| 14 | Last Retry At | Date/Time | |
| 15 | Status | Text (multi-choice) | Pending, Retrying, Resolved, Abandoned |
| 16 | Resolved By | Text | |
| 17 | Resolution Notes | Text | |
| 18 | Date Created | Date/Time | Auto |

---

### Table 4: API Credentials (Connector Config)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | System Name | Text | e.g., "BambooHR", "Jira-PROD" |
| 7 | Auth Type | Text (multi-choice) | API Key, Bearer Token, HMAC Secret, OAuth 2.0, Basic Auth |
| 8 | Credential | Text (multiline) | Masked after save; decrypted at runtime via env var |
| 9 | Base URL | URL | e.g., https://api.bamboohr.com/api/gateway.php/company |
| 10 | Rate Limit (req/min) | Numeric | Enforced by rate_limiter.py |
| 11 | Timeout Seconds | Numeric | |
| 12 | Is Active | Checkbox | |
| 13 | Last Used | Date/Time | Updated on each API call |
| 14 | Total Calls Today | Summary (Events) | |
| 15 | Notes | Text | |

---

### Table 5: Integration Health (Daily Aggregation)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Source System | Text | |
| 7 | Date | Date | One row per system per day |
| 8 | Total Events | Numeric | |
| 9 | Success Count | Numeric | |
| 10 | Failure Count | Numeric | |
| 11 | DLQ Count | Numeric | |
| 12 | Avg Processing Ms | Numeric | |
| 13 | Success Rate | Formula (Numeric) | Success / Total × 100 |
| 14 | Health Status | Formula (Text) | Healthy / Degraded / Down |
| 15 | Health Color | Formula (Text) | Hex color |

---

## Event Lifecycle

```
External System fires webhook
         │
         ▼
  [auth_validator.py]      ← reject if signature invalid (HTTP 401)
         │
         ▼
  [rate_limiter.py]        ← reject if rate limit exceeded (HTTP 429)
         │
         ▼
  [event_logger.py]        ← write event to QB (Status: Received) immediately
         │
         ▼
  Deduplication check      ← if dedup_key seen in last 60s → Status: Skipped, return 200
         │
         ▼
  [router.py]              ← look up route from QB Integration Routes
         │
    ┌────┴────┐
    │         │
No route   Route found
    │         │
Status:  [transformer.py]  ← transform payload to target schema
Skipped       │
              ▼
         [connector.py]   ← deliver to target system
              │
    ┌─────────┴─────────┐
  Success             Failure
    │                   │
Status:          [retry_handler.py] ← retry 1, 2, 4, 8, 16s
Success                 │
                  ┌─────┴─────┐
           Retry OK       Perm Fail
                │               │
           Status:         Dead Letter
           Success          Queue
```

---

## Routing Config Schema (for generic_transformer)

```json
{
  "route_id": "R06",
  "source": "Web Form",
  "event_type": "lead.submitted",
  "target": "Quickbase",
  "target_table": "{{CRM_DEALS_TABLE_ID}}",
  "target_action": "create_record",
  "transformer": "generic_transformer",
  "field_mappings": [
    { "source_path": "firstName",    "target_field": "7",  "type": "string" },
    { "source_path": "lastName",     "target_field": "8",  "type": "string" },
    { "source_path": "email",        "target_field": "10", "type": "email" },
    { "source_path": "company",      "target_field": "14", "type": "string" },
    { "source_path": "dealValue",    "target_field": "16", "type": "number" },
    { "source_path": "leadSource",   "target_field": "21", "type": "string" },
    { "source_path": "$.metadata.submitted_at", "target_field": "22", "type": "datetime" }
  ],
  "static_fields": [
    { "target_field": "15", "value": "New Lead" },
    { "target_field": "25", "value": "Web Form" }
  ]
}
```
