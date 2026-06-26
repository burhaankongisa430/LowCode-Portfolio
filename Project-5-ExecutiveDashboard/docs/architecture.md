# Architecture & Data Model

## KPI Definitions & Data Lineage

### Domain 1: Operational (Service Desk)
Source: `ServiceDeskAutomation` Quickbase app

| KPI | Field Source | Calculation |
|-----|-------------|-------------|
| SLA Met Rate | Tickets[SLA Status] | COUNT(Met) / COUNT(Resolved or Closed) |
| Active Breaches | Tickets[SLA Status] | COUNT where SLA Status = "Breached" and not closed |
| Avg Resolution Hours | Tickets[Resolution Time Hours] | AVG where Status in (Resolved, Closed) |
| Open Ticket Count | Tickets[Status] | COUNT where Status not in (Resolved, Closed) |
| P1 Breach Count | Tickets[Priority, SLA Status] | COUNT P1-Critical where SLA Status = Breached and open |
| Ticket Volume WoW | Tickets[Date Created] | COUNT this week / COUNT last week |
| First Response SLA Rate | Tickets[First Response Date, First Response Due] | COUNT met / COUNT with response |

### Domain 2: Commercial (CRM / Sales)
Source: `CRM-System` Quickbase app

| KPI | Field Source | Calculation |
|-----|-------------|-------------|
| Weighted Pipeline Value | Deals[Weighted Value] | SUM where not closed |
| Won Revenue MTD | Deals[Deal Value, Actual Close Date, Stage] | SUM Won this calendar month |
| Win Rate | Deals[Stage] | COUNT Won / COUNT (Won + Lost) |
| Avg Sales Cycle Days | Deals[Deal Age Days, Stage] | AVG where Won |
| Quota Attainment % | Sales Reps[Won This Month, Quota] | SUM Won / SUM Quota |
| Stalled Deals | Deals[Deal Health Label] | COUNT where Stalled and not closed |
| Pipeline Coverage Ratio | Deals, Reps | Weighted Pipeline / Total Quota |

### Domain 3: People (HR / Onboarding)
Source: `EmployeeOnboarding` Quickbase app

| KPI | Field Source | Calculation |
|-----|-------------|-------------|
| Active Onboarding Count | Employees[Onboarding Status] | COUNT Active or Pre-boarding |
| On Track Rate | Employees[Onboarding Health] | COUNT On Track / COUNT Active |
| Avg Completion Days | Employees[Days Since Start, Status] | AVG where Completed |
| Day 1 Readiness Rate | Employees[AD Account Created, M365 License Assigned] | COUNT both true / COUNT started |
| Overdue Tasks Total | Onboarding Tasks[Is Overdue] | COUNT true and not closed |
| Delayed Hires Count | Employees[Onboarding Health] | COUNT Delayed |
| Completed This Month | Employees[Onboarding Status, Date Created] | COUNT Completed and modified this month |

### Domain 4: Finance (Procurement)
Source: `ProcurementWorkflow` Quickbase app

| KPI | Field Source | Calculation |
|-----|-------------|-------------|
| Committed Spend MTD | Purchase Requests[Total Amount, Date Created] | SUM where not Rejected/Canceled this month |
| Avg Budget Utilization | Budget Codes[Utilization %] | AVG across active budget codes |
| Avg Approval Cycle Days | Approval History[Response Time Hours] | SUM / 24 |
| Pending Approvals | Purchase Requests[Status] | COUNT where Status contains "Pending" |
| Approval SLA Breach Count | Purchase Requests[SLA Breached] | COUNT true |
| Unapproved Vendor Requests | Purchase Requests[Vendor Approved] | COUNT false and not rejected |
| Rejection Rate | Purchase Requests[Status] | COUNT Rejected / COUNT (Approved + Rejected) |

---

## Quickbase KPI Snapshots Table

Stores a point-in-time record of all KPIs every 15 minutes. Powers trend analysis.

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Snapshot ID | Formula (Text) | "SNAP-" & ToText([Record ID#]) |
| 7 | Snapshot Time | Date/Time | Set at ETL run |
| 8 | Snapshot Date | Formula (Date) | Date([Snapshot Time]) |
| 9 | Week Number | Formula (Numeric) | WeekOfYear([Snapshot Time]) |
| 10 | ETL Duration Seconds | Numeric | How long the ETL took |
| 11 | Health Score | Numeric | 0–100 composite |
| 12 | Health Status | Formula (Text) | Excellent/Good/Needs Attention/At Risk/Critical |
| 13 | Health Color | Formula (Text) | Hex color |
| 14 | Operational Score | Numeric | 0–100 |
| 15 | Commercial Score | Numeric | 0–100 |
| 16 | People Score | Numeric | 0–100 |
| 17 | Finance Score | Numeric | 0–100 |
| 18 | SLA Met Rate | Numeric | % |
| 19 | Active Breaches | Numeric | |
| 20 | Avg Resolution Hours | Numeric | |
| 21 | Open Tickets | Numeric | |
| 22 | Weighted Pipeline | Numeric | Currency |
| 23 | Won Revenue MTD | Numeric | Currency |
| 24 | Win Rate | Numeric | % |
| 25 | Quota Attainment | Numeric | % |
| 26 | Stalled Deals | Numeric | |
| 27 | Active Onboarding | Numeric | |
| 28 | Onboarding On Track Rate | Numeric | % |
| 29 | Avg Completion Days | Numeric | |
| 30 | Day1 Readiness Rate | Numeric | % |
| 31 | Committed Spend MTD | Numeric | Currency |
| 32 | Avg Budget Utilization | Numeric | % |
| 33 | Pending Approvals | Numeric | |
| 34 | Approval Cycle Days | Numeric | |
| 35 | Domains Available | Numeric | 1–4 (how many source systems responded) |
| 36 | ETL Errors | Text | JSON list of domain errors |

---

## KPI Alert Thresholds (Configurable in config.py)

| KPI | Warning Threshold | Critical Threshold |
|-----|------------------|-------------------|
| Health Score | < 70 | < 55 |
| SLA Met Rate | < 85% | < 70% |
| Active P1 Breaches | > 0 | > 2 |
| Win Rate | < 35% | < 20% |
| Quota Attainment | < 75% | < 50% |
| Onboarding On Track Rate | < 85% | < 70% |
| Budget Utilization (any dept) | > 85% | > 100% |
| Pending Approvals | > 10 | > 25 |

---

## Dataverse Table Schemas

### Table: KPI_Snapshot (matches QB table above — used for Power BI DirectQuery)

| Column | Type | Notes |
|--------|------|-------|
| kpi_snapshot_id | Uniqueidentifier | PK |
| snapshot_time | DateTime | |
| health_score | Decimal | |
| health_status | Text | |
| operational_score | Decimal | |
| commercial_score | Decimal | |
| people_score | Decimal | |
| finance_score | Decimal | |
| [all domain KPIs as columns] | Decimal/Int | One column per KPI |

### Table: KPI_Alert

| Column | Type | Notes |
|--------|------|-------|
| alert_id | Uniqueidentifier | PK |
| alert_time | DateTime | |
| domain | Text | Operational/Commercial/People/Finance/Overall |
| kpi_name | Text | |
| current_value | Decimal | |
| threshold_value | Decimal | |
| severity | Text | Warning / Critical |
| acknowledged | Boolean | |

---

## ETL Pipeline Data Flow

```
Every 15 minutes:
  ┌──────────────────────────────────────────────────────┐
  │  scheduler.py → orchestrates pipeline run            │
  │                                                      │
  │  EXTRACT (parallel, isolated):                       │
  │    service_desk_extractor.py  → domain_data["ops"]  │
  │    crm_extractor.py           → domain_data["crm"]  │
  │    onboarding_extractor.py    → domain_data["hr"]   │
  │    procurement_extractor.py   → domain_data["fin"]  │
  │                                                      │
  │  TRANSFORM:                                          │
  │    kpi_calculator.py          → unified KPI dict    │
  │    → domain scores (0–100)                          │
  │    → composite health score                         │
  │    → alert flags (threshold breaches)               │
  │                                                      │
  │  LOAD (parallel):                                    │
  │    dataverse_loader.py        → Dataverse           │
  │    qb_client.write_snapshot() → QB Snapshots table  │
  │                                                      │
  │  ALERT (if thresholds breached):                    │
  │    POST → Power Automate alert flow                 │
  └──────────────────────────────────────────────────────┘

Every Monday 06:30 SAST:
  report_generator.py → HTML email → Power Automate → execs
```
