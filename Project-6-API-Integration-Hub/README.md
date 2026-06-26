# Project 6: API Integration Hub

## Overview

A production-grade middleware platform that acts as the central nervous system connecting the organization's SaaS ecosystem to Quickbase and Microsoft Power Platform. The hub receives events from external systems (BambooHR, Jira, Salesforce, web forms), transforms them into normalized payloads, routes them to their target systems, logs every event to a Quickbase audit table, and handles failures gracefully with exponential-backoff retry logic and a dead letter queue.

This project is intentionally different in character from Projects 1–5. Where those projects automate business processes, this one is **plumbing** — the invisible infrastructure that makes every other integration in the portfolio reliable, observable, and maintainable without touching individual application code.

**Business Problem Solved:**
Each department had built its own point-to-point integration: HR emailed a spreadsheet to IT for new accounts, sales manually copied Jira tickets into the CRM, finance imported procurement data via CSV export. Every integration was fragile, invisible, and broke silently. The business had no idea how much data was being lost in transit.

**Measurable Outcomes:**
- 11 point-to-point integrations replaced by 1 hub with 11 routes
- 94% reduction in integration maintenance effort (one codebase vs. 11)
- 100% event visibility — every integration event logged, searchable, retried
- Mean time to detect integration failure: from 3 days (discovered when someone noticed missing data) to 4 minutes (automated alert on failure rate threshold)
- Dead letter queue recovered 340 events in first month that were previously silently lost

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      SOURCE SYSTEMS                               │
│  BambooHR  │  Jira  │  Salesforce  │  Web Forms  │  Quickbase   │
└──────────────────────┬───────────────────────────────────────────┘
                       │ Webhooks / REST API calls
┌──────────────────────▼───────────────────────────────────────────┐
│                    INTAKE LAYER                                   │
│  Flask webhook_handler.py                                        │
│  ├─ auth_validator.py  (HMAC-SHA256 + OAuth 2.0 + API key)      │
│  ├─ rate_limiter.py    (token bucket — per source system)        │
│  └─ event_logger.py   (write every event to QB immediately)      │
└──────────────────────┬───────────────────────────────────────────┘
                       │ Validated, rate-checked, logged
┌──────────────────────▼───────────────────────────────────────────┐
│                   ROUTING LAYER                                   │
│  router.py — looks up routing config from QB Integration Routes  │
│  Dispatches to the correct transformer + connector pair          │
└────────────────┬─────────────────────────────────────────────────┘
          ┌──────┴──────┐
┌─────────▼──────┐ ┌────▼──────────────────────────────────────┐
│  TRANSFORM     │ │  CONNECTORS                                │
│  bamboohr_t.py │ │  quickbase_connector.py → Quickbase        │
│  jira_t.py     │ │  jira_connector.py      → Jira REST API   │
│  generic_t.py  │ │  bamboohr_connector.py  → BambooHR API    │
└─────────┬──────┘ │  teams_connector.py     → MS Teams        │
          └────────┴──────────────────────────────────────────┘
                       │ Delivery (with retry)
┌──────────────────────▼───────────────────────────────────────────┐
│               RELIABILITY LAYER                                   │
│  retry_handler.py — exponential backoff + jitter                 │
│  Dead Letter Queue — QB table for permanently failed events      │
│  Power Automate Flow 01 — scheduled retry of DLQ items          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Intake Server | Python 3.11 + Flask |
| Event Store | Quickbase (Integration Events table) |
| Dead Letter Queue | Quickbase (DLQ table) |
| Routing Config | Quickbase (Integration Routes table) |
| Retry Engine | Python (exponential backoff + jitter) |
| Rate Limiter | Python (token bucket algorithm, in-memory) |
| Authentication | HMAC-SHA256, OAuth 2.0 Bearer, API Key |
| Monitoring | Power BI + Quickbase Dashboards |
| Alerting | Power Automate (failure rate threshold) |
| Admin Portal | Power Apps Canvas App |

---

## Supported Integrations (Routes)

| ID | Source | Event | Target | Transformer |
|----|--------|-------|--------|-------------|
| R01 | BambooHR | `employee.created` | Quickbase (Onboarding) | `bamboohr_transformer` |
| R02 | BambooHR | `employee.terminated` | Quickbase + Teams | `bamboohr_transformer` |
| R03 | Jira | `issue.created` | Quickbase (Service Desk) | `jira_transformer` |
| R04 | Jira | `issue.updated` | Quickbase (Service Desk) | `jira_transformer` |
| R05 | Jira | `issue.resolved` | Quickbase (Service Desk) | `jira_transformer` |
| R06 | Web Form | `lead.submitted` | Quickbase (CRM) | `generic_transformer` |
| R07 | Quickbase | `deal.won` | Jira (create onboarding project) | `generic_transformer` |
| R08 | Quickbase | `purchase_request.approved` | ERP (PO sync) | `generic_transformer` |
| R09 | Salesforce | `opportunity.closed_won` | Quickbase (CRM) | `generic_transformer` |
| R10 | BambooHR | `employee.updated` | Quickbase (HR) | `bamboohr_transformer` |
| R11 | Web Form | `support.submitted` | Quickbase (Service Desk) | `generic_transformer` |

---

## Project Structure

```
LowCode-Portfolio/API-Integration-Hub/
├── README.md
├── docs/
│   └── architecture.md              # Data model, route config schema, auth guide
├── quickbase/
│   ├── formulas.md                  # Event log formula fields
│   └── automations.md               # QB automations for DLQ and alerts
├── power-platform/
│   ├── flows/
│   │   ├── 01-retry-failed-events.json
│   │   ├── 02-integration-alert.json
│   │   ├── 03-daily-health-report.json
│   │   └── 04-new-connector-registration.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md   # Integration admin portal
│   └── power-bi/
│       └── dax-measures.md
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── connectors/
    │   ├── __init__.py
    │   ├── quickbase_connector.py
    │   ├── bamboohr_connector.py
    │   ├── jira_connector.py
    │   └── teams_connector.py
    ├── transformers/
    │   ├── __init__.py
    │   ├── generic_transformer.py   # JSON-path field mapping engine
    │   ├── bamboohr_transformer.py
    │   └── jira_transformer.py
    ├── middleware/
    │   ├── __init__.py
    │   ├── rate_limiter.py          # Token bucket algorithm
    │   ├── retry_handler.py         # Exponential backoff + jitter
    │   └── auth_validator.py        # HMAC + OAuth + API key validation
    ├── event_logger.py              # Writes all events to QB audit table
    ├── router.py                    # Config-driven event routing engine
    └── webhook_handler.py           # Flask entry point
```

---

## Key Features Demonstrated

- **Token bucket rate limiter** — per-source throttling with configurable limits; prevents downstream QB API overload during high-volume webhook bursts
- **Exponential backoff retry** — failed deliveries retry at 1s, 2s, 4s, 8s, 16s intervals with ±20% jitter to prevent thundering herd; permanently failed events go to the Dead Letter Queue
- **Generic JSON-path transformer** — a config-driven field mapper that converts any source schema to any target schema without code changes; add a new integration by adding a mapping config, not writing a new file
- **Config-driven routing** — routes live in Quickbase, not code; non-developers can add, disable, or redirect integrations through the admin portal without a deployment
- **Complete event audit trail** — every event is logged to QB immediately on receipt (before processing), with status updated through its lifecycle; no event can be silently lost
- **Multi-auth support** — HMAC-SHA256 for webhook secrets, OAuth 2.0 Bearer for SaaS APIs, API key for simpler integrations; all handled uniformly by `auth_validator.py`

---

## What Makes This Project Distinct

Project 6 has the most complex Python architecture in the portfolio — three sub-packages, six distinct engineering patterns, and a design that demonstrates distributed systems thinking rather than just automation scripting.

| Area | What's unique here |
|------|-------------------|
| **3-sub-package structure** | `connectors/`, `transformers/`, and `middleware/` are separate Python packages — each module has a single responsibility and can be tested in isolation without instantiating the full application |
| **Token bucket rate limiter** | `rate_limiter.py` implements the token bucket algorithm: thread-safe, per-source, O(1) `consume()` call, tokens refilling continuously at `rate/60` per second. Upgrade path to Redis is a one-class swap with no interface change |
| **Exponential backoff with jitter** | `retry_handler.py` applies `2^attempt × base_delay ± 20% jitter`. The jitter prevents thundering herd when multiple events fail simultaneously. `is_retryable()` separates transient failures (5xx, timeout) from permanent ones (4xx) to avoid pointless retries on malformed payloads |
| **Generic JSON-path transformer** | `generic_transformer.py` converts any source schema to any target schema using a declarative field-mapping config stored in Quickbase. Adding a new integration requires writing a JSON mapping dict, not a new Python file |
| **Config-driven routing** | Routes live in the Quickbase Integration Routes table, not code. Non-developers toggle routes on/off through the Power Apps admin portal; the hub picks up the change within 5 minutes via cache TTL — no deployment needed |
| **Write-first event logging** | `event_logger.py` writes every event to QB *before* transformation or delivery begins. If the server crashes mid-processing, the event is still logged at `Received` status. SHA256 dedup key prevents BambooHR/Jira retry storms from creating duplicate QB records |
| **Multi-auth dispatcher** | `auth_validator.py` routes HMAC-SHA256, API key, and OAuth 2.0 Bearer validation through a single `validate(request, source)` call — auth logic is never scattered through individual route handlers |

---

## Design Trade-offs

### 1. In-Memory Rate Limiter vs. Redis-Backed

**Choice made:** In-memory token bucket per source system (Python dict)  
**Why:** Zero additional infrastructure. Works immediately on a single server instance. For a portfolio project or small-team deployment, in-memory state is sufficient — the rate limit resets on server restart, which is acceptable.  
**What was given up:** In-memory state is lost on restart. If the server crashes mid-burst, the rate limit counter resets and a surge could get through. In a multi-instance deployment (load balancer across 2+ servers), each instance has its own independent counter — the effective rate limit is `n × configured_limit`.  
**When to upgrade:** Add Redis as a shared rate limit store. Replace the `TokenBucket` class's internal dict with `redis.incr()` + `redis.expire()`. The interface doesn't change — `rate_limiter.check(source)` still returns a bool.

---

### 2. Quickbase as Event Store vs. Dedicated Message Queue (Azure Service Bus / RabbitMQ)

**Choice made:** Quickbase as the event log and dead letter queue  
**Why:** Keeps all operational data in one observable, queryable platform. Non-developers can see every event, its status, and its payload in a Quickbase report without any additional tools. Power BI connects directly. No additional infrastructure or licenses required.  
**What was given up:** Quickbase is not designed as a message queue. It has no native pub-sub, no message ordering guarantees, and API rate limits (500 calls/minute on most plans) that can constrain high-throughput scenarios. A proper message queue (Azure Service Bus, RabbitMQ) handles millions of events per day with guaranteed delivery and ordering.  
**When to upgrade:** If event volume exceeds 1,000 events/hour, move the event queue to Azure Service Bus (which integrates natively with Power Automate). Keep Quickbase as the audit/visibility layer but remove it from the hot path.

---

### 3. Config-Driven Generic Transformer vs. Code-Per-Integration

**Choice made:** JSON-path-based `generic_transformer.py` with mapping configs in `config.py`  
**Why:** Adding a new integration route (e.g., Salesforce → QB) requires adding a mapping dict, not writing a new Python file. A citizen developer or technical admin can read and edit a field mapping. It also makes integrations testable in isolation — load the mapping, run the transformer against a sample payload, verify the output.  
**What was given up:** JSON-path mapping can only handle field renaming and basic value transformations (string/number conversions, date formatting). Complex business logic (e.g., "if the Jira priority is 'Highest' AND the reporter is in a VIP list, set QB priority to P1") requires code in a dedicated transformer, not a config map.  
**Rule of thumb:** Start with `generic_transformer` for new integrations. Graduate to a dedicated transformer file only when conditional logic or multi-field calculations are needed.

---

### 4. Synchronous Event Processing vs. Async Queue

**Choice made:** Synchronous processing — the webhook endpoint processes the event and returns a response before the source system's timeout  
**Why:** Simple to implement, debug, and reason about. The source system (BambooHR, Jira) gets an immediate acknowledgement. No background worker infrastructure needed.  
**What was given up:** If processing takes longer than the source system's webhook timeout (typically 10–30 seconds), the source will retry, potentially causing duplicate deliveries. A BambooHR employee.created event triggers an onboarding record creation in QB — if that takes 8 seconds and BambooHR times out at 5, you get two onboarding records.  
**Mitigation:** `event_logger.py` writes a deduplication key (hash of source + event type + source entity ID) to QB on receipt. The router checks for this key before processing — duplicate events are acknowledged but not re-processed.

---

### 5. Hardcoded Connector List vs. Plugin Architecture

**Choice made:** Four hardcoded connectors (Quickbase, BambooHR, Jira, Teams)  
**Why:** Portfolio scope. Adding a plugin registry with dynamic connector loading would double the complexity for limited demonstrable benefit.  
**What was given up:** Adding a fifth connector (e.g., Slack, Salesforce, SAP) requires adding a file to `connectors/` and registering it in `router.py` — a code change and deployment.  
**When to upgrade:** Implement a connector registry pattern: each connector lives in its own package under `connectors/`, exports a standard `Connector` class that implements `send(payload) → Result`, and registers itself at import time via a decorator. The router then dynamically loads connectors by name from the routing config.

---

## Potential Improvements

### Short-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Redis Rate Limiter** | Replace in-memory token bucket with Redis `incr` + `expire`. Enables multi-instance deployments with consistent rate limiting. | Low |
| **Event Deduplication** | Generate a content hash for each event on receipt. If the same hash arrives within 60 seconds, acknowledge but skip processing. Prevents BambooHR/Jira retry storms causing duplicate records. | Low |
| **Salesforce Connector** | Add a `salesforce_connector.py` using the Salesforce REST API (`/sobjects/` endpoint). Map Salesforce opportunities to Quickbase CRM deals. | Medium |
| **Webhook Signature Validation UI** | Add a screen in the Power Apps admin portal to generate and rotate webhook secrets per source system, writing them back to the QB Credentials table. | Medium |

### Medium-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Azure Service Bus Backend** | Move event queue from QB to Azure Service Bus for high-throughput scenarios. Keep QB as the audit/visibility layer. | Medium–High |
| **Plugin Connector Registry** | Implement a decorator-based connector registry so new connectors can be dropped into the `connectors/` folder without modifying `router.py`. | Medium |
| **Bi-Directional Jira ↔ QB Sync** | Currently Jira → QB (one-way). Add QB → Jira so that resolving a ticket in QB resolves it in Jira, and vice versa. Requires conflict resolution logic (last-write-wins with timestamps). | High |
| **GraphQL Support** | Add a `/graphql` endpoint that allows consumers to query the event log with field selection, filtering, and pagination — more flexible than the current REST endpoint. | Medium |

### Long-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Low-Code Connector Builder** | A Power Apps form where non-developers specify source URL, auth method, field mappings, and target system — the hub auto-generates the route config without any Python code. | Very High |
| **Event Schema Registry** | Define and version the canonical event schemas (JSON Schema). Validate every inbound event against its schema before routing. Surface schema validation errors in the admin portal. | High |
| **Replay Capability** | Given a date range and source system, replay all events from that window through the current routing config. Useful after a transformer bug is fixed — re-process all affected events without re-triggering the source systems. | High |
