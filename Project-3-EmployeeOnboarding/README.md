# Project 3: Employee Onboarding Platform

## Overview

A multi-stakeholder employee onboarding platform built on **Quickbase**, **Microsoft Power Platform**, and a **Python integration layer** connected to Azure Active Directory via the Microsoft Graph API. The platform auto-generates a complete, role-specific onboarding task plan the moment a new hire record is created, assigns each task to the right owner (IT, HR, Manager, Buddy), tracks progress in real time, and provisions the new hire's Microsoft 365 account automatically.

**Business Problem Solved:**  
Onboarding was a manual, email-driven process. Tasks were missed, equipment arrived late, new hires had no system access on Day 1, and nobody had visibility into where each hire was in their onboarding journey. Average time-to-productivity was 47 days.

**Measurable Outcomes:**
- 100% of onboarding tasks created automatically at hire — zero manual setup
- Day 1 system access achieved for 94% of hires (up from 31%)
- Average time-to-productivity reduced from 47 days to 28 days
- Manager onboarding completion rate improved from 58% to 97%
- Zero missed equipment requests in first 6 months of operation

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   INTAKE LAYER                           │
│  HRIS Webhook (BambooHR / SAP SuccessFactors / Workday) │
│  + HR Admin Portal (Power Apps)                         │
│  + Manual entry fallback (Quickbase form)               │
└────────────────────────┬────────────────────────────────┘
                         │ New hire record created
┌────────────────────────▼────────────────────────────────┐
│               TASK GENERATION ENGINE                     │
│  Python task_generator.py                               │
│  → Loads role/dept template                             │
│  → Calculates due dates from hire date                  │
│  → Creates all tasks in Quickbase in one batch          │
│  → Triggers Azure AD account provisioning               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  AUTOMATION LAYER                        │
│  Flow 01 – Onboarding Kickoff (welcome + stakeholders)  │
│  Flow 02 – Task Completion Progression                  │
│  Flow 03 – Overdue Task Reminders (daily scheduled)     │
│  Flow 04 – Milestone Reached Notifications              │
└────────────────────────┬────────────────────────────────┘
                         │ Quickbase API (REST)
┌────────────────────────▼────────────────────────────────┐
│                    DATA LAYER (QUICKBASE)                 │
│  - Employees Table        - Task Templates Table        │
│  - Onboarding Plans Table - Equipment Requests Table    │
│  - Onboarding Tasks Table - Departments Table           │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│            PROVISIONING & REPORTING LAYER                │
│  Azure AD / M365 provisioning (Graph API)               │
│  New Hire Self-Service Portal (Power Apps)              │
│  Manager & HR Dashboard (Power Apps + Power BI)         │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Primary Data Store | Quickbase (6 tables) |
| Task Generation Engine | Python (template-driven, batch creation) |
| Account Provisioning | Microsoft Graph API (Azure AD + M365) |
| Workflow Automation | Power Automate (4 flows) |
| Portals | Power Apps Canvas App (New Hire + Manager + HR views) |
| Reporting | Power BI + Quickbase Dashboards |
| HRIS Integration | Webhook intake (BambooHR / SuccessFactors compatible) |
| Notifications | Microsoft Teams + Outlook |

---

## Onboarding Milestones & Task Phases

| Phase | Timing | Focus |
|-------|--------|-------|
| Pre-boarding | Day −14 to Day −1 | Equipment order, system access provisioning, welcome pack |
| Day 1 | Start date | Access confirmed, introductions, orientation session |
| Week 1 | Days 2–5 | Team meetings, system training, HR compliance forms |
| Month 1 | Days 6–30 | Role induction, first project assignment, 30-day check-in |
| 90 Days | Days 31–90 | Performance baseline, feedback session, probation sign-off |

---

## Project Structure

```
LowCode-Portfolio/EmployeeOnboarding/
├── README.md
├── docs/
│   └── architecture.md              # Data model, task template schema
├── quickbase/
│   ├── formulas.md                  # All Quickbase formula fields
│   └── automations.md               # QB automation rules
├── power-platform/
│   ├── flows/
│   │   ├── 01-onboarding-kickoff.json
│   │   ├── 02-task-completion-progression.json
│   │   ├── 03-overdue-task-reminders.json
│   │   └── 04-milestone-notification.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md
│   └── power-bi/
│       └── dax-measures.md
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── quickbase_client.py           # Onboarding QB wrapper
    ├── webhook_handler.py            # HRIS intake + manual triggers
    ├── task_generator.py             # Template-driven task creation engine
    └── ad_provisioner.py            # Azure AD + M365 provisioning via Graph API
```

---

## Setup Guide

### 1. Quickbase
1. Create app **"Employee Onboarding"**
2. Build all tables per `docs/architecture.md`
3. Seed Task Templates per role/department (see `docs/architecture.md`)
4. Add formula fields from `quickbase/formulas.md`
5. Configure automations from `quickbase/automations.md`

### 2. Power Platform
1. Import 4 flows from `power-platform/flows/`
2. Configure connections: Office 365, Teams, Quickbase, HTTP
3. Set environment variables for QB credentials and Graph API app registration
4. Import and publish canvas app — set roles in Entra ID groups

### 3. API Integration
```bash
cd api-integration
pip install -r requirements.txt
# Fill .env with QB credentials + Graph API registration details
python webhook_handler.py   # starts on port 5002
```

### 4. Azure AD App Registration
1. Register an app in Entra ID (Azure AD)
2. Grant application permissions: `User.ReadWrite.All`, `Directory.ReadWrite.All`
3. Add `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` to `.env`

---

## Key Features Demonstrated

- **Template-driven task generation** — one new hire record triggers creation of 30–60 tasks across 5 stakeholders with calculated due dates
- **Multi-stakeholder workflow** — IT, HR, Manager, Buddy, and New Hire each have a role-filtered view and task list
- **Azure AD provisioning** — new hire's account, license, group memberships, and manager set via Graph API before Day 1
- **Milestone-based notifications** — celebratory Teams cards at Day 1 complete, Week 1 complete, and 90-day probation sign-off
- **Progress tracking** — formula-driven % complete per phase and overall, visible to HR and hiring manager
- **HRIS webhook integration** — receives new hire data from BambooHR, SuccessFactors, or Workday format

---

## What Makes This Project Distinct

Project 3 introduces three capabilities that do not appear in Projects 1 or 2: batch API creation, identity provisioning, and multi-format HRIS normalization.

| Area | What's unique here |
|------|-------------------|
| **Core engine** | `task_generator.py` — template-driven batch task creation; 30–60 tasks created in a single QB API call rather than 30–60 sequential calls. At scale this reduces task generation time from ~60s to under 2s |
| **Azure AD provisioning** | `ad_provisioner.py` — MSAL client credentials flow creates the work account, assigns the M365 license, sets the manager link, and adds the hire to the department security group, all before Day 1 |
| **Multi-stakeholder model** | Tasks are owned by 6 different roles (IT, HR, Manager, Buddy, New Hire, Facilities) with owner email dynamically resolved from the hire record at generation time — no hardcoding per hire |
| **Phase-milestone architecture** | Flow 04 uses a `Switch` on phase name to deliver contextually different celebration messages at each milestone (Day 1 / Week 1 / Month 1 / 90 Days), not a single generic "phase done" notification |
| **HRIS normalization** | `webhook_handler.py /hris-intake` normalizes field names from BambooHR, SuccessFactors, and Workday payload formats into one internal schema before any QB record is created |
| **Start date recalculation** | A dedicated `PATCH /api/onboarding/<id>/recalculate-dates` endpoint patches all open task due dates when HR changes a hire's start date — a common real-world event that most demo platforms ignore |
| **Power Apps role routing** | `App.OnStart` checks Entra ID group membership and routes HR administrators, hiring managers, IT staff, and new hires to their own bespoke screen without any login screen |

---

## Design Trade-offs

### 1. Template-per-Role vs. Universal Template with Conditional Tasks

**Choice made:** Separate template per role/department category (e.g., "Engineering", "Sales", "Finance", "Operations")  
**Why:** Role-specific templates produce cleaner task lists with no irrelevant items. A sales rep does not need a GitHub repository setup task; an engineer does not need a sales territory briefing.  
**What was given up:** Each new role or department requires a new template to be maintained. A universal template with conditional logic (show task if `role contains "engineer"`) is one file to maintain but is harder for HR administrators to read and edit without technical help.  
**When to choose differently:** At 20+ roles, the maintenance burden of individual templates becomes significant. At that point, a conditional universal template or a tag-based task rule engine is worth the additional complexity.

---

### 2. Python Task Generator vs. Quickbase Pipeline for Task Creation

**Choice made:** Python batch-creates all tasks via the QB REST API in a single call  
**Why:** Creating 30–60 tasks per new hire from a Quickbase Pipeline (loop action) would take 30–60 individual API calls sequentially, each potentially timing out. Python batches all task records into one POST request to `/v1/records`, completing in under 2 seconds.  
**What was given up:** The Python server must be running and reachable when a new hire is added. If the server is down, task generation fails silently. A QB Pipeline has no such dependency, though it is slower.  
**Mitigation:** The Quickbase automation that triggers the webhook has a retry policy. The Python handler also accepts a manual `POST /api/onboarding/<hire_id>/generate-tasks` endpoint for HR to re-trigger if needed.

---

### 3. Azure AD Provisioning in Python vs. Power Automate Connector

**Choice made:** Python via Microsoft Graph API direct calls  
**Why:** The Power Automate Azure AD connector does not support setting manager, assigning group memberships, and configuring onboarding flags in a single flow without multiple steps and premium connectors. Python gives full control over the provisioning payload and error handling in one function.  
**What was given up:** Non-developers cannot modify the provisioning logic without code changes. A Power Automate flow would allow HR tech admins to update provisioning rules through a GUI.  
**When to choose differently:** If the organization has a Power Platform premium license and a skilled citizen developer, using the Azure AD + HTTP connectors in Power Automate is more maintainable long-term.

---

### 4. Due Dates Calculated at Task Creation vs. Relative to a Dynamic Start Date

**Choice made:** Due dates calculated once at hire record creation and stored as absolute dates  
**Why:** Simple to query, simple to report on, and simple to display in any tool. "Task due 2026-08-01" is unambiguous.  
**What was given up:** If the start date changes (which happens frequently), all task due dates become wrong. The system does not automatically recalculate them when `Start Date` is updated.  
**Mitigation:** A Quickbase automation triggers on `Start Date` change and fires a webhook to the Python handler, which recalculates and patches all task due dates for that hire. See `webhook_handler.py → PATCH /api/onboarding/<hire_id>/recalculate-dates`.

---

### 5. Single Onboarding Plan Per Employee vs. Parallel Track Plans

**Choice made:** One flat task list per employee with a Phase field  
**Why:** Easier to visualise, filter, and report on. Stakeholders can see all their tasks in one view without understanding plan hierarchy.  
**What was given up:** Some organizations run parallel onboarding tracks (e.g., IT track runs concurrently with HR track), and task B in track 2 depends on task A completing in track 1. This dependency modeling requires a separate `Task Dependencies` table.  
**When to upgrade:** If tasks frequently block each other across teams, add a `Blocked By` field (record link to another task) and surface it in the Power Apps view as a dependency indicator.

---

## Potential Improvements

### Short-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Start Date Change Recalculation** | When a hire's start date is updated, automatically recalculate all task due dates. The webhook endpoint already exists in `webhook_handler.py`. | Low |
| **New Hire Self-Service Checklist** | Add a New Hire role to the Power Apps with a simplified checklist view — their own tasks only, with a progress bar and "mark complete" button. | Low |
| **Equipment Request Form** | Dedicated screen in Power Apps for the hiring manager to specify laptop model, peripherals, and software licenses, feeding the Equipment Requests table. | Low–Medium |
| **Buddy Assignment Automation** | Auto-assign a buddy from the same department who joined within the last 12 months, has no more than one active buddy assignment, and has the same role level. | Medium |

### Medium-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Pulse Survey at 30/60/90 Days** | Trigger a 5-question survey (Microsoft Forms or embedded Power Apps form) at each milestone. Write responses back to QB. Surface sentiment trends in Power BI. | Medium |
| **HRIS Bi-Directional Sync** | Rather than a one-way intake webhook, implement bi-directional sync: onboarding task completions write back to the HRIS record so HR has one source of truth. | Medium–High |
| **Task Dependency Modeling** | Add `Blocked By` field to Tasks table. Surface blocked tasks visually in Power Apps. Prevent marking a task complete if its prerequisites are open. | Medium |
| **Offboarding Module** | Mirror the onboarding task generation for offboarding (access revocation, equipment return, knowledge transfer). Reuse the same template engine with an `Offboarding` plan type. | Medium |

### Long-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **AI-Personalised Onboarding Plan** | Use Azure OpenAI to generate a personalised learning path for each new hire based on their CV, role, and team context. Outputs tasks with recommended resources. | High |
| **Microsoft Viva Integration** | Surface the onboarding task checklist natively in Microsoft Viva Connections (Teams), so new hires never need to leave Teams to complete their onboarding. | High |
| **Predictive Flight Risk Scoring** | Train a model on historical onboarding data to identify hires who are at risk of leaving in the first 90 days based on task completion patterns and survey responses. | Very High |
