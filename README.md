# Low-Code Developer Portfolio

A portfolio of seven low-code/no-code solutions built on **Quickbase**, **Microsoft Power Platform**, and **Python**, demonstrating end-to-end delivery of business automation, system integration, and executive reporting across four operational domains.

Each project folder contains its own detailed README covering architecture, tech stack, setup guide, design trade-offs, and potential improvements.

---

## Portfolio at a Glance

| # | Project | Domain | Primary Challenge |
|---|---------|--------|-------------------|
| 1 | [Service Desk Automation](#project-1-service-desk-automation) | IT Operations | Ticket routing, SLA tracking, escalation |
| 2 | [CRM & Sales Pipeline](#project-2-crm--sales-pipeline) | Sales | Lead management, pipeline forecasting |
| 3 | [Employee Onboarding](#project-3-employee-onboarding) | HR | Multi-stakeholder task orchestration, Azure AD provisioning |
| 4 | [Procurement Approval](#project-4-procurement-approval) | Finance | Multi-level human approvals, budget validation, PO generation |
| 5 | [Executive KPI Dashboard](#project-5-executive-kpi-dashboard) | Leadership | Cross-system KPI aggregation, org health scoring |
| 6 | [API Integration Hub](#project-6-api-integration-hub) | Infrastructure | Middleware, event routing, retry logic, dead letter queue |
| 7 | [Digital Transformation Case Study](#project-7-digital-transformation-case-study) | Business Case | ROI measurement, before/after analysis, program narrative |

---

## Project Summaries

### Project 1: Service Desk Automation

**Folder:** `Project-1-ServiceDeskAutomation/`

An automated IT service desk built on Quickbase and Power Automate. Tickets are submitted via a Power Apps portal, email, or webhook; a Python Flask layer validates and ingests them; and four Power Automate flows handle routing, SLA monitoring, escalation, and notifications.

**What it demonstrates:** Relational data modeling in Quickbase, multi-step Power Automate flows (conditions, parallel branches, error scopes), REST API integration with Quickbase and Microsoft Graph, and real-time SLA reporting in Power BI.

**Key outcomes:** SLA breach rate cut from 34% to under 6%; average resolution time reduced by 41%.

---

### Project 2: CRM & Sales Pipeline

**Folder:** `Project-2-CRM-System/`

A custom-built CRM managing the full sales lifecycle — lead capture through to won/lost — with automated follow-up reminders, a rule-based lead scoring engine, and weighted pipeline forecasting.

**What it demonstrates:** Multi-table relational modeling (Contacts → Companies → Deals → Activities → Products), a Python lead-scoring engine, automated email/calendar activity ingestion via Microsoft Graph, and pipeline analytics in Power BI.

**How it differs from Project 1:** Where Project 1 focuses on internal IT operations, Project 2 models an external-facing commercial process with a more complex data model, a scoring algorithm, and revenue-oriented analytics.

**Key outcomes:** Deals lost to missed follow-up reduced by 63%; forecast accuracy improved from ±40% to ±12%.

---

### Project 3: Employee Onboarding

**Folder:** `Project-3-EmployeeOnboarding/`

A multi-stakeholder onboarding platform that auto-generates a complete, role-specific task plan (30–60 tasks across IT, HR, Manager, Buddy, and Facilities) the moment a new hire record is created, and provisions their Microsoft 365 account via Azure Active Directory before Day 1.

**What it demonstrates:** Template-driven batch API creation (all tasks created in a single QB API call), Azure AD provisioning via the Microsoft Graph API using MSAL, multi-format HRIS webhook normalization (BambooHR, SuccessFactors, Workday), and role-based screen routing in Power Apps.

**How it differs from Projects 1–2:** This is the first project that reaches outside Microsoft 365 to provision an external identity system (Azure AD). It also introduces the concept of a task template engine — one record triggers the creation of dozens of downstream records — which is not a pattern used in the earlier projects.

**Key outcomes:** Day 1 system access achieved for 94% of hires (up from 31%); time-to-productivity cut from 47 to 28 days.

---

### Project 4: Procurement Approval

**Folder:** `Project-4-ProcurementWorkflow/`

A multi-level purchase approval platform where requests are routed through up to four approval levels (Manager → Department Head → Finance Director → CEO) based on spend amount. Approvers respond directly from email or Microsoft Teams — no portal login required. Approved requests automatically generate a purchase order and sync to the finance/ERP system.

**What it demonstrates:** The Power Automate native Approvals connector (suspend-until-human-responds pattern), amount-based conditional routing logic, atomic budget reservation to prevent double-spending, HTML purchase order generation in Python, and an ERP-agnostic connector design.

**How it differs from Projects 1–3:** Projects 1–3 automate processes that run without human intervention once triggered. Project 4's centerpiece is a human decision — making the approval experience frictionless (approve from email) is the core design challenge, not the automation itself.

**Key outcomes:** Average approval cycle reduced from 8.3 days to 1.4 days; 100% of approved requests generate a PO automatically.

---

### Project 5: Executive KPI Dashboard

**Folder:** `Project-5-ExecutiveDashboard/`

An intelligence layer that sits above Projects 1–4. A Python ETL pipeline extracts KPIs from all four operational Quickbase apps every 15 minutes, computes a composite Organizational Health Score (weighted across Operational, Commercial, People, and Finance domains), loads the results into Microsoft Dataverse, and delivers insights via a six-page Power BI dashboard, a mobile Power Apps viewer, and an automated weekly HTML report emailed every Monday morning.

**What it demonstrates:** Multi-source ETL with parallel extraction (ThreadPoolExecutor), Dataverse as a Power BI DirectQuery staging layer, a transparent weighted scoring engine with tunable domain weights, HTML executive report generation, and cross-domain correlation analysis in Power BI.

**How it differs from Projects 1–4:** This is the only project that does not automate a business process — it aggregates the outputs of all four process systems to answer a single question: "How is the business performing right now?" It introduces multi-source ETL orchestration, APScheduler, and a dual-store (Quickbase + Dataverse) architecture that none of the earlier projects required.

**Key outcomes:** Four weekly reports collapsed into one; executive meeting prep reduced from 3 hours to 20 minutes.

---

### Project 6: API Integration Hub

**Folder:** `Project-6-API-Integration-Hub/`

A middleware platform that replaces eleven point-to-point integrations with a single hub. It receives webhook events from external SaaS systems (BambooHR, Jira, Salesforce, web forms), validates and rate-limits them, transforms payloads using a config-driven JSON-path mapper, routes them to the correct target connector, and handles failures via exponential-backoff retry and a dead letter queue — all with every event logged to Quickbase before processing begins.

**What it demonstrates:** Token bucket rate limiting, exponential backoff with jitter, config-driven routing (routes stored in Quickbase, not code), multi-auth dispatch (HMAC-SHA256, OAuth 2.0, API key), write-first event logging for crash safety, and a three-sub-package Python architecture (connectors, transformers, middleware).

**How it differs from Projects 1–5:** All previous projects are business applications — they model a domain (tickets, deals, employees, spend, KPIs) and automate workflows within it. Project 6 is infrastructure. It has no business domain of its own; its job is to make every other integration reliable, observable, and maintainable without touching individual application code. It is the most technically complex Python project in the portfolio.

**Key outcomes:** Mean time to detect integration failure reduced from 3 days to 4 minutes; 340 previously silently lost events recovered in the first month via the dead letter queue.

---

### Project 7: Digital Transformation Case Study

**Folder:** `Project-7-DigitalTransformationCaseStudy/`

A documented 18-month digital transformation program for a fictional professional services firm (Meridian Professional Services, 280 employees, R120M revenue) that delivered all six preceding platforms in two phases. This project provides the business narrative, discovery methodology, before/after measurement data, and financial ROI analysis that ties the entire portfolio together.

**What it demonstrates:** AS-IS → TO-BE process analysis, stakeholder mapping, time-in-motion study methodology, phased delivery planning, financial ROI calculation (NPV, payback period, sensitivity analysis), and executive-quality reporting.

**How it differs from Projects 1–6:** Projects 1–6 are technical deliverables. Project 7 is the business case that justifies them. It answers the questions a hiring manager or client cares most about: *What problem did you actually solve? How did you measure success? What was the financial return?* It also surfaces the lessons learned and change management challenges that pure technical documentation omits.

**Key outcomes:** Total annual benefits of R8.1M against a R1.95M investment; 316% ROI with a 2.9-month payback period.

---

## How the Projects Relate to Each Other

```
┌──────────────────────────────────────────────────────────────────────┐
│  PROJECT 7: Digital Transformation Case Study                         │
│  (Business narrative, ROI, discovery — wraps the entire portfolio)   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  PROJECT 5: Executive KPI Dashboard                                   │
│  (Intelligence layer — aggregates KPIs from Projects 1–4)            │
└──────┬─────────────────┬────────────────────┬─────────────────┬──────┘
       │                 │                    │                 │
┌──────▼──────┐  ┌───────▼──────┐  ┌─────────▼──────┐  ┌──────▼──────┐
│ Project 1   │  │  Project 2   │  │   Project 3    │  │  Project 4  │
│ Service     │  │  CRM &       │  │   Employee     │  │  Procurement│
│ Desk        │  │  Sales       │  │   Onboarding   │  │  Approval   │
└──────┬──────┘  └───────┬──────┘  └─────────┬──────┘  └──────┬──────┘
       │                 │                    │                 │
       └─────────────────┴────────────────────┴─────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  PROJECT 6: API Integration Hub                                       │
│  (Infrastructure layer — connects all systems to external SaaS)      │
└──────────────────────────────────────────────────────────────────────┘
```

Projects 1–4 are independent operational systems, each solving a different departmental problem. Project 5 sits above them as the reporting intelligence layer. Project 6 sits below them as the integration infrastructure layer. Project 7 provides the business context for the whole program.

---

## Common Technology Stack

All seven projects share the same core technology foundation:

| Layer | Technology |
|-------|-----------|
| Data Store | Quickbase (tables, formula fields, automations, reports) |
| Workflow Automation | Microsoft Power Automate |
| User Interface | Microsoft Power Apps (Canvas Apps) |
| Reporting & Analytics | Microsoft Power BI |
| API Integration | Python 3.11 + Flask |
| Notifications | Microsoft Teams + Outlook (Office 365) |
| Authentication | OAuth 2.0 (Power Platform) + Quickbase User Token |

Individual projects layer additional technologies on top of this base — see each project's README for the full tech stack.

---

## Detailed Documentation

Each project folder contains a `README.md` with:

- Full architecture diagram
- Complete tech stack table
- Step-by-step setup guide
- Key features demonstrated
- Design trade-offs (what was chosen, why, and when to choose differently)
- Potential improvements (short, medium, and long-term)

Navigate to the relevant folder to read the detailed documentation for any project.
