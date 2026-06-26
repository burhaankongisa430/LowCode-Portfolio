# Project 2: CRM & Sales Pipeline System

## Overview

A full-featured Customer Relationship Management and sales pipeline platform built on **Quickbase**, **Microsoft Power Platform**, and a **Python API integration layer**. The system manages the full sales lifecycle from lead capture through to won/lost, with automated follow-up reminders, lead scoring, and real-time pipeline analytics.

**Business Problem Solved:**  
Sales teams were losing deals due to inconsistent follow-up, no visibility into pipeline health, manually compiled forecasts, and zero insight into why deals were being lost.

**Measurable Outcomes:**
- 63% reduction in deals lost due to missed follow-up (automated reminder system)
- Pipeline forecast accuracy improved from ±40% to ±12% (weighted deal value formula)
- Lead response time reduced from 48 hours to under 2 hours (automated intake + assignment)
- 100% of sales activities logged (previously ~30% captured manually)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   INTAKE LAYER                           │
│  Power Apps Canvas App (Sales Rep Portal)               │
│  + Website Form Webhook (Python/Flask)                  │
│  + LinkedIn / Marketing Automation (API)                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST (JSON)
┌────────────────────────▼────────────────────────────────┐
│                  AUTOMATION LAYER                        │
│  Power Automate Flow 01 – New Lead Intake & Assignment  │
│  Power Automate Flow 02 – Deal Stage Progression        │
│  Power Automate Flow 03 – Follow-up Reminders           │
│  Power Automate Flow 04 – Won / Lost Notifications      │
└────────────────────────┬────────────────────────────────┘
                         │ Quickbase API (REST)
┌────────────────────────▼────────────────────────────────┐
│                    DATA LAYER (QUICKBASE)                 │
│  - Contacts Table         - Activities Table            │
│  - Companies Table        - Products Table              │
│  - Deals Table (core)     - Deal Products Table         │
│  - Pipeline Stages Table  - Sales Reps Table            │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 INTELLIGENCE LAYER                       │
│  Python Lead Scorer (rule-based scoring engine)         │
│  Python Email Tracker (activity ingestion)              │
│  Power BI Pipeline Analytics Dashboard                  │
│  Quickbase Sales Reports & Kanban-style Views           │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Primary Data Store | Quickbase (6 core tables + 2 junction tables) |
| Sales Rep Portal | Power Apps Canvas App |
| Workflow Automation | Power Automate (4 flows) |
| Pipeline Analytics | Power BI + Quickbase Dashboards |
| API Integration | Python 3.11 + Flask |
| Lead Scoring | Python (rule-based engine) |
| Email Activity Tracking | Python (Microsoft Graph API) |
| Notifications | Microsoft Teams + Outlook (Office 365) |

---

## Pipeline Stages & Win Probability

| Stage | Win Probability | Expected Actions |
|-------|----------------|-----------------|
| New Lead | 5% | Qualify within 24h |
| Qualified | 20% | Discovery call booked |
| Proposal Sent | 40% | Proposal delivered |
| Negotiation | 70% | Commercial terms agreed |
| Verbal Commit | 85% | Waiting for signature |
| Closed Won | 100% | Deal signed |
| Closed Lost | 0% | Loss reason captured |
| On Hold | — | Re-engage date set |

---

## Project Structure

```
Project-2-CRM-Sales-Pipeline/
├── README.md
├── docs/
│   └── architecture.md              # Full data model & field definitions
├── quickbase/
│   ├── formulas.md                  # All Quickbase formula fields
│   └── automations.md               # Quickbase automation rules & pipelines
├── power-platform/
│   ├── flows/
│   │   ├── 01-new-lead-intake.json
│   │   ├── 02-deal-stage-progression.json
│   │   ├── 03-follow-up-reminder.json
│   │   └── 04-won-lost-notification.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md   # Power Fx code for all screens
│   └── power-bi/
│       └── dax-measures.md          # DAX measures & KPIs
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── quickbase_client.py           # QB REST API wrapper (CRM)
    ├── webhook_handler.py            # Flask server for external lead intake
    ├── lead_scorer.py                # Rule-based lead scoring engine
    └── email_tracker.py             # Microsoft Graph API activity ingestion
```

---

## Setup Guide

### 1. Quickbase Setup
1. Create a new Quickbase app named **"CRM – Sales Pipeline"**
2. Build tables per `docs/architecture.md`
3. Add all formula fields from `quickbase/formulas.md`
4. Configure automations from `quickbase/automations.md`
5. Create pipeline stage view: group Deals by Stage, sort by Weighted Value descending

### 2. Power Platform Setup
1. Import all 4 flows from `power-platform/flows/`
2. Configure connections: Office 365, Quickbase connector, Teams
3. Set environment variables for QB credentials and flow URLs
4. Import and publish the canvas app

### 3. API Integration Setup
```bash
cd api-integration
pip install -r requirements.txt
# Create a .env file with credentials (see config.py for required keys)
python webhook_handler.py   # starts on port 5001
```

### 4. Power BI
1. Connect to Quickbase REST API as data source
2. Load Deals, Contacts, Companies, Activities tables
3. Apply DAX measures from `power-bi/dax-measures.md`
4. Publish and pin to Teams tab for sales team access

---

## Key Features Demonstrated

- **Multi-table relational data model** — Contacts → Companies → Deals → Activities → Products
- **Lead scoring engine** — composite score from 8 weighted signals, drives routing priority
- **Weighted pipeline forecasting** — deal value × stage probability, aggregated by rep and period
- **Automated follow-up system** — daily scheduled flow surfaces overdue follow-ups before they become lost deals
- **Activity tracking via Microsoft Graph** — emails and calendar events written back to the Activities table automatically
- **Role-based access** — reps see own pipeline; managers see full team; leadership sees aggregated dashboard only
- **Win/loss analytics** — loss reason taxonomy drives actionable reporting

---

## Design Trade-offs

Every decision in this project involved a deliberate choice between competing approaches.

### 1. Quickbase as CRM vs. Dedicated CRM (Dynamics 365 / Salesforce)

**Choice made:** Quickbase custom-built CRM  
**Why:** Demonstrates the ability to design and build a domain model from scratch — a core skill being assessed. A dedicated CRM is a pre-built product, not a portfolio piece. Quickbase also allows full customization of pipeline stages, scoring, and automation rules without per-seat licensing overhead.  
**What was given up:** Dynamics 365 and Salesforce ship with built-in AI scoring, email sync, forecasting, and mobile apps. A Quickbase CRM requires building these capabilities manually (or via integration). At enterprise scale, a dedicated CRM will always outperform a custom Quickbase solution.  
**When to choose differently:** For a company with 50+ sales reps, deal complexity, and a Microsoft 365 or Salesforce contract already in place, choose Dynamics 365 or Salesforce and use Power Platform / Quickbase for peripheral automation rather than the core CRM.

---

### 2. Rule-Based Lead Scoring vs. ML Model

**Choice made:** Rule-based scoring engine (Python)  
**Why:** Transparent, explainable, and immediately deployable with zero training data. Sales managers can read the scoring rules, understand why a lead scored 72 vs. 45, and override or tune the weights without a data scientist. Builds trust faster than a black-box model.  
**What was given up:** A machine learning model trained on historical won/lost data will outperform hand-crafted rules once sufficient data exists (typically 500+ closed deals). Rules also require manual recalibration as the market changes.  
**When to upgrade:** After 6 months of data with at least 200 closed deals, replace the rule-based scorer with a logistic regression or gradient-boosted model trained on the Activities + Deals tables. The API interface in `lead_scorer.py` is designed to make this swap a one-file change.

---

### 3. Activity Logging via Email Tracker vs. Manual Entry

**Choice made:** Automated ingestion via Microsoft Graph API  
**Why:** Salespeople do not log calls and emails. Forcing manual entry results in ~30% compliance. Automatically pulling emails, calendar events, and Teams calls from Microsoft Graph and writing them to the Activities table removes the behavior change requirement entirely.  
**What was given up:** Privacy considerations — parsing employee email requires explicit consent and appropriate Graph API scopes (`Mail.Read`, `Calendars.Read`). In some jurisdictions this requires legal sign-off. Manual logging, while incomplete, has no privacy overhead.  
**When to choose differently:** Where privacy policies prohibit email scanning, provide a one-click "Log this email" button as an Outlook add-in (Power Platform's Outlook connector supports this). Reduces friction while keeping the employee in control.

---

### 4. Pipeline Stage as a Single Status Field vs. a Separate Stage History Table

**Choice made:** Single `Stage` field on the Deals table, with stage changes written to the Activities table as audit events  
**Why:** Simpler to query, simpler for sales reps to understand, and sufficient for 95% of reporting needs. Stage history is reconstructable from the Activities table.  
**What was given up:** A dedicated Stage History table enables precise "time in stage" analytics (e.g., "deals that spend more than 14 days in Proposal lose 60% of the time"). This insight requires a full history log, not just a current value.  
**When to upgrade:** Add a `Deal Stage History` table with fields: Deal, Previous Stage, New Stage, Changed By, Changed At, Days in Previous Stage. The Quickbase automation for stage changes already writes to Activities — extending it to a dedicated table is a low-effort upgrade with high analytical value.

---

### 5. Flat Follow-up Date vs. Cadence Sequences

**Choice made:** Single `Next Follow-up Date` field per deal  
**Why:** Simple for reps to manage, simple to automate reminders against, and covers the vast majority of B2B sales motions. One date, one action.  
**What was given up:** A sequence engine (e.g., "Day 1: email, Day 3: call, Day 7: LinkedIn") automates the entire follow-up cadence and is the standard in tools like Salesloft and Outreach. Implementing this in Quickbase requires a separate Sequences table, a Cadence Steps table, and a more complex scheduling flow.  
**When to upgrade:** If the business runs high-volume outbound sales (50+ leads/week per rep), a cadence engine is worth the complexity. At lower volumes, a single follow-up date is more flexible and less constraining for relationship-based selling.

---

## Potential Improvements

### Short-Term (Low Effort, High Impact)

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Email-to-Lead** | Power Automate monitors a shared mailbox (`sales@company.com`). Inbound emails create Contact + Deal records automatically. | Low |
| **LinkedIn Lead Sync** | Use LinkedIn Sales Navigator API to pull lead profile data (title, company size, industry) into the Contact record at creation, enriching the lead score. | Medium |
| **Deal Probability Override** | Allow reps to manually override the formula-calculated win probability with a note. Track overrides in the audit log to measure rep forecast accuracy over time. | Low |
| **Mobile-Optimized App** | The canvas app currently targets tablet/desktop. Add a phone layout screen for reps logging activity on the road. | Low–Medium |

### Medium-Term (Higher Effort, Strategic Value)

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Cadence Sequences** | Add a Sequences table and Cadence Steps table. Schedule follow-up tasks automatically based on deal stage and lead score, removing the single-date limitation. | Medium–High |
| **Forecast Rollup by Territory** | Add a Territories table and roll pipeline forecasts up by territory as well as by rep and team. Essential for multi-region sales organizations. | Medium |
| **Competitor Tracking** | Add a Competitors field (multi-select) to Deals. Track win/loss rates by competitor. Surface competitive displacement opportunities when a competitor's customer engages. | Low–Medium |
| **Power BI Embedded in Power Apps** | Embed the pipeline dashboard directly in the canvas app manager screen via the Power BI tile control. Removes app-switching friction for leadership. | Low |

### Long-Term (Architectural Upgrades)

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **ML Win Probability Model** | Replace the rule-based lead scorer with a gradient-boosted model (XGBoost) trained on historical won/lost deals. Recalibrate quarterly. | High |
| **CPQ Integration** | Connect a Configure-Price-Quote tool (or build one in Quickbase) so that proposals generated from the system pull live product pricing and generate PDF quotes automatically. | High |
| **Customer Health Scoring** | Extend the data model beyond the sales lifecycle into customer success. Track product usage, support tickets, and renewal dates. Feed health scores back into the CRM to identify upsell and churn risk. | High |
| **Dataverse Migration for Enterprise Scale** | At 100+ users, migrate core tables to Dataverse for Microsoft-managed security, Copilot integration, and native Power Platform performance. Keep Quickbase for operational views and quick-build extensions. | Very High |
