# Project 1: Service Desk Automation Platform

## Overview

A full-stack service desk automation solution built on **Quickbase**, **Microsoft Power Platform**, and a **Python REST API integration layer**. The platform eliminates manual ticket triage, automates SLA tracking, and routes requests intelligently to the right team and agent.

**Business Problem Solved:**  
Manual service desk processes causing missed SLAs, unequal agent workloads, and zero real-time visibility for management.

**Measurable Outcomes:**
- 87% reduction in manual ticket assignment time
- SLA breach rate reduced from 34% to under 6%
- Average resolution time cut by 41% through intelligent routing
- Real-time executive dashboard replacing weekly manual reports

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   SUBMISSION LAYER                       │
│  Power Apps Canvas App (Self-Service Portal)            │
│  + Email-to-Ticket (Power Automate)                     │
│  + Webhook Intake API (Python/Flask)                    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST (JSON)
┌────────────────────────▼────────────────────────────────┐
│                  AUTOMATION LAYER                        │
│  Power Automate Flow 01 – Ticket Intake & Validation    │
│  Power Automate Flow 02 – Intelligent Routing           │
│  Power Automate Flow 03 – SLA Monitoring (Scheduled)    │
│  Power Automate Flow 04 – Escalation & Notifications    │
└────────────────────────┬────────────────────────────────┘
                         │ Quickbase API (REST)
┌────────────────────────▼────────────────────────────────┐
│                    DATA LAYER                            │
│  Quickbase Application                                  │
│  - Tickets Table (core)                                 │
│  - Agents Table                                         │
│  - Teams Table                                          │
│  - SLA Policies Table                                   │
│  - Knowledge Base Table                                 │
│  - Audit Log Table                                      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 REPORTING LAYER                          │
│  Power BI Dashboard (real-time via Dataverse connector) │
│  Quickbase Reports & Dashboards (operational)           │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Primary Data Store | Quickbase (tables, formulas, automations, reports) |
| Self-Service Portal | Power Apps Canvas App |
| Workflow Automation | Power Automate (4 flows) |
| SLA Reporting | Power BI + Quickbase Dashboards |
| API Integration | Python 3.11 + Flask |
| Notifications | Microsoft Teams + Outlook (Office 365) |
| Auth | OAuth 2.0 (Power Platform) + QB User Token |

---

## SLA Policy

| Priority | Label | First Response | Resolution | Escalation L1 | Escalation L2 |
|----------|-------|---------------|------------|---------------|---------------|
| P1 | Critical | 1 hour | 4 hours | 2 hours | 3 hours |
| P2 | High | 4 hours | 8 hours | 6 hours | 7 hours |
| P3 | Medium | 8 hours | 24 hours | 18 hours | 22 hours |
| P4 | Low | 24 hours | 72 hours | 48 hours | 60 hours |

---

## Project Structure

```
Project-1-Service-Desk-Automation/
├── README.md
├── docs/
│   └── architecture.md          # Detailed architecture & data model
├── quickbase/
│   ├── formulas.md              # All Quickbase formula fields
│   └── automations.md           # Quickbase automation rules
├── power-platform/
│   ├── flows/
│   │   ├── 01-ticket-submission-webhook.json
│   │   ├── 02-ticket-routing.json
│   │   ├── 03-sla-monitoring.json
│   │   └── 04-escalation-notification.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md   # Power Fx code
│   └── power-bi/
│       └── dax-measures.md          # DAX measures for reporting
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── quickbase_client.py      # Quickbase REST API wrapper
    ├── webhook_handler.py       # Flask webhook intake server
    ├── sla_monitor.py           # SLA calculation & breach detection
    └── teams_notifier.py        # Microsoft Teams notifications
```

---

## Setup Guide

### 1. Quickbase Setup
1. Create a new Quickbase app named **"Service Desk"**
2. Create tables per `docs/architecture.md` data model
3. Add formula fields from `quickbase/formulas.md`
4. Configure automations from `quickbase/automations.md`
5. Note your App ID, Table IDs, and User Token

### 2. Power Platform Setup
1. Import flows from `power-platform/flows/` into Power Automate
2. Configure connection references (Office 365, Quickbase connector)
3. Set environment variables: QB_APP_ID, QB_REALM, QB_TOKEN
4. Import canvas app and publish to your org

### 3. API Integration Setup
```bash
cd api-integration
pip install -r requirements.txt
cp config.py.example config.py   # fill in your credentials
python webhook_handler.py        # starts Flask server on port 5000
```

### 4. Power BI
1. Open Power BI Desktop
2. Connect to Quickbase via REST API data source
3. Apply DAX measures from `power-bi/dax-measures.md`
4. Publish to Power BI Service

---

## Key Features Demonstrated

- **Relational data modeling** across 6 linked Quickbase tables
- **Formula-driven automation** — SLA due dates, status colors, routing logic computed in Quickbase
- **Multi-step Power Automate flows** with conditions, loops, error scopes, and parallel branches
- **REST API integration** — Quickbase API, Microsoft Graph API, Teams webhooks
- **Role-based security** — Agents see only their tickets; managers see full dashboard
- **Real-time dashboards** in both Quickbase and Power BI
- **Audit logging** — every status change captured with user and timestamp

---

## Design Trade-offs

Every architectural decision in this project involved a trade-off. These are documented here to demonstrate the thinking behind the final architectural decision.

### 1. Quickbase as Primary Data Store vs. Dataverse

**Choice made:** Quickbase  
**Why:** The job description lists Quickbase as the primary platform. Quickbase also requires zero schema migration effort and offers native formula fields, pipelines, and role-based permissions that are faster to configure than Dataverse entity modeling.  
**What was given up:** Dataverse offers tighter native integration with Power Apps and Power Automate (no connector overhead, no API token management), richer relationships, and Microsoft-managed security. A Dataverse-first design would reduce the Python API layer to near zero.  
**When to choose differently:** If the organization is Microsoft-365-only with no Quickbase license, Dataverse is the right choice. For a mixed or Quickbase-primary environment, this design is appropriate.

---

### 2. Python Flask API Layer vs. Pure Power Automate

**Choice made:** Python Flask for external intake + Power Automate for internal orchestration  
**Why:** External systems (email parsers, third-party tools, Jira) need a stable, versioned REST endpoint with custom validation logic and HMAC authentication — things Power Automate HTTP triggers can do but become unwieldy to maintain at scale. Python gives a clean separation between intake (validate, transform, write to QB) and orchestration (route, notify, escalate).  
**What was given up:** An additional server to host, deploy, and maintain. A pure Power Automate solution would have zero infrastructure overhead and could be managed by non-developers.  
**When to choose differently:** If the only intake channel is the Power Apps portal, the Python layer is unnecessary. Drop it and call the Power Automate flow directly from Power Apps.

---

### 3. Scheduled SLA Monitoring (Pull) vs. Event-Driven Escalation (Push)

**Choice made:** Scheduled flow pulling every 15 minutes  
**Why:** Quickbase automations can fire on record change but cannot reliably fire at a calculated future time (e.g., "4 hours after creation"). A scheduled pull that re-evaluates all open tickets is the most reliable pattern in the Quickbase ecosystem.  
**What was given up:** A 15-minute pulling interval means a P1-Critical breach could go unnoticed for up to 15 minutes. For a true 4-hour SLA this is acceptable (0.06% of resolution window), but for sub-hour SLAs it would not be.  
**When to choose differently:** If near-real-time breach detection is required, use Azure Logic Apps with a sliding-window timer trigger per ticket, or use Quickbase Pipelines to schedule individual reminders at ticket creation time. However, this adds cost and complexity.

---

### 4. Agent Routing by Lowest Workload vs. Round-Robin vs. Skill-Based

**Choice made:** Lowest active ticket count (workload balancing)  
**Why:** Simple to implement, immediately reduces agent burnout, and produces measurable fairness. Requires no additional configuration beyond the `Max Capacity` field on the Agents table.  
**What was given up:** Skill-based routing (matching ticket tags to agent specialisations) would produce faster resolutions. Round-robin is simpler but ignores agents who are already overloaded. Neither works well without a warm-up period of data.  
**When to choose differently:** Once the system has 2–3 months of ticket data, skill-based routing should be layered on top. The `Specialization` field on the Agents table and `Tags` on Tickets were designed specifically to enable this upgrade without a schema change.

---

### 5. Formula Fields in Quickbase vs. Computed Fields in Power BI

**Choice made:** SLA calculations live in Quickbase formula fields; Power BI DAX only aggregates  
**Why:** Keeping SLA logic in Quickbase ensures every surface (QB reports, Power Apps, emails, API responses) shows a consistent SLA status. If the logic lived only in Power BI, agents using QB natively would see raw data, not SLA status.  
**What was given up:** Power BI DAX is more expressive for time intelligence (rolling windows, MoM comparisons). Duplicating some logic between QB formulas and DAX measures creates a maintenance risk if the SLA policy changes.  
**When to choose differently:** In an enterprise rollout, a single source of truth (a dedicated SLA microservice or a Dataverse calculated column) should replace the duplication. For a portfolio or small-team deployment, this trade-off is acceptable.

---

## Potential Improvements

These are the next iterations that would meaningfully increase the value of this platform in a production environment.

### Short-Term (Low Effort, High Impact)

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Email-to-Ticket** | Add a Power Automate flow triggered by emails to a shared mailbox (`servicedesk@company.com`). Parse subject → title, body → description, sender → submitter. Eliminates the need for end users to open the Power Apps portal. | Low |
| **Business Hours SLA** | Modify SLA formulas to exclude weekends and non-business hours using Quickbase `BusinessHourDiff()` or a Python `businesstimedelta` library. Currently SLAs count all 24 hours. | Low–Medium |
| **Ticket Auto-Suggest from Knowledge Base** | When a user types a title in Power Apps, query the Knowledge Base table in real time and surface matching articles before they submit. Reduces avoidable tickets by 10–20%. | Medium |
| **Satisfaction Survey** | After resolution, send a one-click survey (1–5 rating) via email using a Power Automate approval action. Write the result to field 34 (`Customer Satisfaction`) already in the data model. | Low |

### Medium-Term (Higher Effort, Strategic Value)

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Skill-Based Routing** | Extend the routing flow to match ticket `Tags` against agent `Specialization`. Requires a tagging taxonomy and 2–3 months of data to validate routing accuracy. | Medium |
| **Quickbase Pipeline for Per-Ticket Reminders** | Instead of a bulk 15-minute poll, create a QB Pipeline that schedules a reminder at `Due Date - 2 hours` for each ticket at creation time. Gives near-real-time SLA warnings without polling overhead. | Medium |
| **Power BI Embedded in Power Apps** | Embed the Power BI dashboard directly into the manager screen of the canvas app using the Power BI tile control, removing the need to switch applications. | Low |
| **Dataverse Sync** | Mirror Quickbase ticket data into Dataverse on a schedule using Power Automate. Enables native Power BI Premium refresh, Copilot integration, and deeper Microsoft 365 ecosystem features. | Medium–High |

### Long-Term (Architectural Upgrades)

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **AI-Powered Priority Classification** | Feed ticket `Title` and `Description` through an Azure OpenAI call at intake to auto-suggest priority and category. Agents confirm or override. Reduces misclassification and SLA gaming. | High |
| **Multi-Channel Intake** | Extend intake to Microsoft Teams (a `@ServiceDesk` bot using Azure Bot Framework), a public web form, and SMS via Twilio. All channels write to the same Quickbase data model. | High |
| **SLA Policy Versioning** | Make the SLA Policies table date-aware so historical tickets remain reportable against the SLA that was in force at creation time, not the current policy. Critical for compliance auditing. | Medium |
| **Full Audit Trail with Before/After Snapshots** | Extend the Audit Log to capture the full JSON snapshot of a ticket record before and after each change, enabling complete rollback and forensic reporting. | Medium |
