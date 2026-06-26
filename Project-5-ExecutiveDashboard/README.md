# Project 5: Executive KPI Dashboard

## Overview

A cross-platform executive intelligence layer that aggregates KPIs from all four operational Quickbase applications (Service Desk, CRM, Employee Onboarding, Procurement), computes a composite Organizational Health Score, and delivers insights via a **Power BI dashboard**, a **mobile Power Apps KPI viewer**, and an **automated weekly HTML executive report** emailed every Monday morning.

This project is intentionally different in character from Projects 1–4. Where those projects automate business processes, this one sits *above* all of them — it is the intelligence layer that answers the question: **"How is the business performing right now?"**

**Business Problem Solved:**
Leadership had no unified view of operations. Reporting was manual, inconsistent, and always one to two weeks stale. The CEO received four separate emails from four department heads every Monday, each formatted differently. There was no way to see whether a dip in sales was correlated with a spike in service desk tickets or delayed onboarding.

**Measurable Outcomes:**
- 4 separate weekly reports collapsed into 1 unified dashboard
- Decision-making data available in real time vs. 5–7 days lag
- First cross-domain correlation identified within 2 weeks: high procurement approval delays correlated with IT SLA breaches (blocked equipment orders)
- Executive meeting prep time reduced from 3 hours to 20 minutes

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     SOURCE SYSTEMS                              │
│  QB: ServiceDeskAutomation  │  QB: CRM-System                 │
│  QB: EmployeeOnboarding     │  QB: ProcurementWorkflow + ERP  │
└────────────────┬───────────────────────────────────────────────┘
                 │  Python ETL (extract via QB REST API)
┌────────────────▼───────────────────────────────────────────────┐
│                  TRANSFORMATION LAYER (Python)                  │
│  4 domain extractors → kpi_calculator.py → unified KPI dict    │
│  Computes: domain scores, health score, trends, alerts          │
└────────────────┬───────────────────────────────────────────────┘
          ┌──────┴──────┐
          │             │
┌─────────▼──────┐  ┌───▼────────────────────────────────────┐
│  QB KPI        │  │  Microsoft Dataverse (via Graph API)    │
│  Snapshots     │  │  KPI_Snapshots, Domain_Scores tables    │
│  Table         │  │  (Power BI native connector)            │
└─────────┬──────┘  └───┬────────────────────────────────────┘
          │             │
┌─────────▼─────────────▼────────────────────────────────────────┐
│                   PRESENTATION LAYER                            │
│  Power BI Dashboard (6 pages — realtime via DirectQuery)       │
│  Power Apps Mobile KPI Viewer (exec on-the-go)                 │
│  Automated HTML Report (Power Automate, Monday 06:30 SAST)     │
│  KPI Alert emails (threshold breach notifications)              │
└────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Data Extraction | Python 3.11 (4 domain extractors, QB REST API) |
| KPI Calculation | Python (`kpi_calculator.py` — weighted scoring) |
| Primary Analytics Store | Microsoft Dataverse (Power BI DirectQuery) |
| Secondary Store | Quickbase KPI Snapshots table (trend history) |
| Dashboard | Power BI (6-page workbook, published to Power BI Service) |
| Mobile Viewer | Power Apps Canvas App (exec KPI card view) |
| Report Delivery | Power Automate (HTML email + Teams post) |
| Scheduling | APScheduler (ETL every 15 min; full report weekly) |
| Alerts | Power Automate (threshold-based trigger flows) |

---

## KPI Domains & Health Score

### Domain Scoring (each 0–100)

| Domain | Weight | Key Signal |
|--------|--------|-----------|
| Operational (Service Desk) | 25% | SLA met rate, active breaches |
| Commercial (Sales/CRM) | 30% | Pipeline coverage, win rate, quota attainment |
| People (HR/Onboarding) | 20% | On-track rate, time-to-productivity |
| Finance (Procurement) | 25% | Budget utilization, approval cycle time |

### Overall Health Score Formula
```
HealthScore = (Operational × 0.25) + (Commercial × 0.30)
            + (People × 0.20)      + (Finance × 0.25)
```

| Score | Status | Color |
|-------|--------|--------|
| 85–100 | Excellent | #27AE60 |
| 70–84  | Good | #2ECC71 |
| 55–69  | Needs Attention | #F39C12 |
| 40–54  | At Risk | #E67E22 |
| 0–39   | Critical | #E74C3C |

---

## Project Structure

```
LowCode-Portfolio/ExecutiveDashboard/
├── README.md
├── docs/
│   └── architecture.md              # KPI definitions, thresholds, data lineage
├── quickbase/
│   ├── formulas.md                  # KPI Snapshots table formula fields
│   └── automations.md               # Scheduled ETL trigger automation
├── power-platform/
│   ├── flows/
│   │   ├── 01-weekly-etl-trigger.json
│   │   ├── 02-kpi-alert-thresholds.json
│   │   ├── 03-executive-report-email.json
│   │   └── 04-dataverse-sync.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md   # Mobile exec KPI viewer
│   └── power-bi/
│       └── dax-measures.md          # All DAX for 6-page dashboard
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── extractors/
    │   ├── __init__.py
    │   ├── service_desk_extractor.py
    │   ├── crm_extractor.py
    │   ├── onboarding_extractor.py
    │   └── procurement_extractor.py
    ├── kpi_calculator.py             # Domain scoring + health score engine
    ├── report_generator.py           # HTML executive report builder
    ├── dataverse_loader.py          # Push KPIs to Dataverse
    ├── scheduler.py                  # APScheduler ETL orchestration
    └── webhook_handler.py            # Flask API + manual trigger endpoints
```

---

## Dashboard Pages (Power BI)

| Page | Audience | Key Visuals |
|------|----------|------------|
| 1. Executive Summary | CEO / Board | Health score gauge, 4 domain cards, trend sparklines, alert banner |
| 2. Operational (Service Desk) | COO | SLA rates, ticket volume trend, breach heatmap by team |
| 3. Commercial (Sales) | CRO / VP Sales | Pipeline funnel, quota attainment by rep, win/loss by source |
| 4. People (HR) | CHRO | Onboarding health, headcount trend, time-to-productivity scatter |
| 5. Finance (Procurement) | CFO | Spend vs budget by dept, approval cycle waterfall, vendor spend Pareto |
| 6. Cross-Domain Correlations | All Exec | Scatter plots of domain score pairs, shared trend timeline |

---

## Setup Guide

### 1. Quickbase
1. Create a new Quickbase app **"Executive Dashboard"** (or use existing apps)
2. Build the KPI Snapshots table per `docs/architecture.md`
3. Add formula fields from `quickbase/formulas.md`

### 2. Dataverse
1. Create a Dataverse environment (or use existing Power Platform environment)
2. Create tables: `KPI_Snapshot`, `Domain_Score`, `KPI_Alert`
3. Grant the API service principal `System Customizer` role

### 3. API Integration
```bash
cd api-integration
pip install -r requirements.txt
# Fill .env with all 4 QB app credentials + Dataverse details
python webhook_handler.py   # starts on port 5004
# OR: python scheduler.py   # headless scheduled runner
```

### 4. Power BI
1. Connect to Dataverse via the native connector (DirectQuery mode)
2. Connect to the QB KPI Snapshots table via REST API
3. Apply all DAX from `power-bi/dax-measures.md`
4. Publish to Power BI Service → pin to Teams tab for exec team

### 5. Power Automate
1. Import 4 flows from `power-platform/flows/`
2. Configure schedule (weekly 06:30 Monday, threshold alerts ad-hoc)
3. Set executive distribution list in environment variables

---

## Key Features Demonstrated

- **Multi-source ETL pipeline** — 4 domain extractors with unified output schema, error isolation per domain
- **Weighted composite scoring** — transparent, tunable health score with domain weights in `config.py`
- **Dataverse as analytics staging layer** — enables Power BI DirectQuery with sub-minute refresh
- **Automated executive HTML report** — self-contained email with embedded charts (no attachment to open)
- **Threshold-based KPI alerts** — proactive notification when any KPI crosses a defined red line
- **Cross-domain correlation analysis** — Power BI scatter plots and shared timeline reveal systemic issues invisible in siloed dashboards
- **Graceful degradation** — if one source system is unavailable, the ETL continues for the other 3 and flags the missing domain rather than failing entirely

---

## What Makes This Project Distinct

Project 5 is the only project in the portfolio that *consumes* the other four. It sits above all of them as the intelligence layer — and the Python architecture reflects that scope.

| Area | What's unique here |
|------|-------------------|
| **Purpose** | The first project that is not a standalone system — it aggregates data from Projects 1–4 and answers "how is the business performing right now?" in a single number |
| **Python structure** | An `extractors/` sub-package with 4 isolated domain modules. Each extractor runs in its own thread via `ThreadPoolExecutor` — if one source system goes down, the other 3 still produce results and the missing domain is flagged, not silently omitted |
| **ETL orchestration** | `scheduler.py` is a standalone pipeline orchestrator: extract (parallel) → transform → load to QB + Dataverse (parallel) → trigger PA flows → send report. Runs headless via APScheduler or exposes endpoints via Flask |
| **Scoring engine** | `kpi_calculator.py` is fully documented and tunable — domain weights and KPI targets live in `config.py`, not hardcoded. Each scoring formula is named, weighted, and mathematically transparent so a business analyst can recalibrate it without touching code |
| **HTML report generator** | `report_generator.py` produces a self-contained, mobile-responsive HTML email with health score, domain score cards, per-domain score bars, and an alert table — zero external dependencies, no image attachments, no PDF to open |
| **Dataverse as staging layer** | `dataverse_loader.py` writes directly to Dataverse via the Web API using MSAL client credentials, enabling Power BI DirectQuery with near-real-time refresh rather than the 30-min minimum of QB Import mode |
| **Cross-domain correlation** | Power BI Page 6 contains scatter plots of domain score pairs across time — the only visualisation in the portfolio that can surface a systemic issue (e.g., procurement delays causing IT SLA breaches) that siloed dashboards cannot |

---

## Design Trade-offs

### 1. Dataverse as Analytics Layer vs. Direct QB REST API in Power BI

**Choice made:** Dataverse as a staging layer, with the Python ETL pipeline writing snapshots to it  
**Why:** Power BI's Quickbase connector uses Import mode, which means data is stale until the next scheduled refresh (minimum 30 minutes in Power BI Service). Writing KPIs to Dataverse enables DirectQuery mode, giving near-real-time data without waiting for Power BI refresh cycles. Dataverse also lets multiple Power BI datasets share the same source without each making independent QB API calls.  
**What was given up:** Dataverse requires a Power Platform Premium license. It also introduces a staging hop — if the ETL pipeline fails, the dashboard shows stale data. Direct QB connection is simpler to maintain.  
**When to choose differently:** For small teams or budget-constrained environments, skip Dataverse entirely and connect Power BI directly to each QB app via Import mode with a 1-hour refresh. Lose near-real-time but eliminate infrastructure complexity.

---

### 2. Python ETL vs. Power Automate Flows for Data Extraction

**Choice made:** Python ETL pipeline for extraction and transformation; Power Automate only for delivery (email, Teams, alerts)  
**Why:** Power Automate's loop and transformation capabilities are limited for complex multi-source aggregation. A flow that queries 4 QB apps, joins the results, computes a weighted score, and formats an HTML report would be near-impossible to maintain. Python is the right tool for ETL — readable, testable, version-controllable.  
**What was given up:** The Python server requires infrastructure to host. A pure Power Automate approach has no additional hosting cost and is accessible to citizen developers for modification.  
**When to choose differently:** For a simple 2-metric dashboard, Power Automate flows calling QB APIs and writing to Dataverse is perfectly adequate. The Python approach pays off when you have 20+ KPIs, complex scoring logic, or multiple source systems.

---

### 3. Snapshot History Table vs. Live Query Every Time

**Choice made:** KPI snapshots written to QB and Dataverse on every ETL run (every 15 minutes)  
**Why:** Trend analysis requires historical data. If Power BI only queries live data, you can answer "what is the health score now?" but not "how has the health score trended over the last 90 days?" Snapshots enable time-series analysis, week-over-week comparisons, and anomaly detection without re-querying the source systems.  
**What was given up:** Storage grows over time. At 96 runs per day × 365 days = ~35,000 rows per year in the snapshot table. Quickbase has record limits per app on lower tiers.  
**Mitigation:** Add a monthly archival job that aggregates daily snapshots into single monthly records for data older than 3 months, keeping the table size manageable.

---

### 4. Composite Health Score vs. Separate Domain Scores Only

**Choice made:** Single composite Organizational Health Score plus individual domain scores  
**Why:** Executives need one number to answer "is the business healthy?" — four domain scores still require mental aggregation. The composite score enables a red/amber/green indicator on every surface (email subject, Teams status, mobile app). The domain breakdown explains the why.  
**What was given up:** A single number can mask divergent signals — a score of 65 could mean all domains are at 65, or one domain is at 0 and another at 100. The dashboard must always show domain breakdown alongside the composite.  
**Tunable:** Domain weights and KPI thresholds live in `config.py`, not hardcoded. A business analyst can recalibrate the model without touching any extraction or presentation code.

---

### 5. HTML Email Report vs. PDF Attachment vs. Power BI Subscription

**Choice made:** Inline HTML email (no attachment)  
**Why:** Executives open email on mobile. A PDF attachment requires downloading and opening a separate app. An embedded HTML report renders immediately, is searchable, and displays correctly on any screen size. Power BI email subscriptions are limited to static screenshots with no interactivity.  
**What was given up:** HTML emails cannot replicate complex Power BI visualisations. The email shows summary cards and trend tables, not full charts. Executives who want deeper analysis must open the Power BI dashboard.  
**When to upgrade:** If chart rendering in email is a priority, use a Python charting library (Matplotlib, Plotly) to generate PNG chart images and embed them as base64 in the HTML email body.

---

## Potential Improvements

### Short-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Embedded Charts in Email** | Generate PNG sparklines using Matplotlib, embed as base64 in the weekly HTML report. Removes the need to open Power BI for trend context. | Medium |
| **Alert Digest vs. Individual Alerts** | Instead of one email per threshold breach, batch all alerts into a single daily digest at 08:00. Reduces notification fatigue for leadership. | Low |
| **Power BI Teams Tab** | Publish the dashboard to Teams as a tab in the exec channel. Leadership never needs to leave Teams to see KPIs. | Low |
| **Slack Integration** | Post the Monday morning summary to a `#exec-kpis` Slack channel using a Slack webhook — for organizations that run on Slack rather than Teams. | Low |

### Medium-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Anomaly Detection** | Use Python's `statsmodels` library to run ARIMA on each KPI time series. Alert when a value deviates more than 2σ from the rolling average. | Medium–High |
| **Forecast Tab in Power BI** | Use Power BI's built-in forecast feature on the trend line for each KPI to project 4-week forward estimates. | Low |
| **Goal / Target Tracking** | Add a Targets table to Dataverse. Display actual vs. target in Power BI with a bullet chart or variance indicator. | Medium |
| **Mobile Push Notifications** | When the health score drops below a threshold, send a mobile push notification via Power Automate to the CEO's phone (Power Apps mobile app required). | Medium |

### Long-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Natural Language Query** | Integrate Power BI Q&A or Azure OpenAI so executives can ask "why did the health score drop this week?" and receive a plain-English explanation. | High |
| **Copilot Integration** | Surface the KPI snapshot data in Microsoft Copilot for Microsoft 365, allowing executives to ask questions about business performance directly in Teams chat. | High |
| **Board-Level Reporting Pack** | Auto-generate a formal board report (PDF) on the last Friday of each month, combining KPI trends with narrative commentary. Requires a document generation tool (Docmosis, Carbone, or Word automation). | High |
| **External Benchmark Integration** | Pull industry benchmark data from an external API (e.g., ServiceNow benchmarks, Gartner data) and plot company KPIs against industry median in Power BI. | Very High |
