# Transformation Scope — Process Analysis

## Discovery Methodology

Before any tool was selected, six weeks were spent on process discovery:

1. **Stakeholder interviews** — 18 people across 4 departments (30–60 min each)
2. **Time-in-motion studies** — Shadow sessions with each team for 2–3 days
3. **Email & document analysis** — 3 months of historical email threads for process reconstruction
4. **Pain point voting** — Each team scored their top 5 pain points on impact × frequency
5. **Process mapping** — AS-IS swimlane diagrams for every core workflow

Key discovery tool: the **Friction Audit** — a structured survey where staff scored each step in their daily workflow on a 1–5 friction scale. Steps scoring 4+ became the primary automation targets.

---

## Domain 1: Service Desk (Project 1)

### Before State — AS-IS Process

```
Customer emails IT inbox
        │
        ▼ (sometimes hours later)
IT agent reads email
        │
        ▼
Manually creates ticket in shared spreadsheet
        │
        ▼
Agent guesses priority based on subject line
        │
        ▼
Forwards to "correct" person via email
        │
        ▼ (no tracking)
Resolution (or not) — no SLA clock
        │
        ▼
Agent manually updates spreadsheet
        │
        ▼ (weekly)
Manager compiles Word doc for management meeting
```

**Friction points identified:**
- No SLA visibility until it was already breached
- Priority assigned by gut feel, not rule
- Agents spent 14h/week on admin (routing, updating, reporting)
- Management had zero real-time visibility
- 34% of tickets missed SLA — discovered *after the fact*

### After State — TO-BE Process (Project 1)

```
Customer submits via Power Apps portal OR email
        │
        ▼ (< 1 minute)
Auto-created in Quickbase with SLA clock running
        │
        ▼ (immediate)
Auto-routed to correct team/agent by category
        │
        ▼
Agent notified via Teams Adaptive Card + email
        │
        ▼ (15-min monitor)
SLA monitoring flow checks all open tickets
        │
    ┌───┴────────────────┐
At Risk          Breached → escalation
notification           notification to manager + agent
    │
    ▼
Agent resolves → auto-confirmation to customer
        │
        ▼
Power BI dashboard updates in real time
```

**Process redesign decisions:**
- SLA priority driven by *category + stated impact*, not agent judgment
- Routing configured in Quickbase (non-technical admins can change it)
- Agents see only their queue — no cross-team noise
- Manager dashboard replaces the weekly Word document entirely

---

## Domain 2: CRM & Sales Pipeline (Project 2)

### Before State — AS-IS Process

```
Lead inquiry arrives (email / LinkedIn / cold call)
        │
        ▼ (manually, 24–48h later)
Sales rep creates row in shared Excel "CRM"
        │
        ▼
No consistent fields, no follow-up reminders
        │
        ▼ (weekly)
Manager consolidates reps' spreadsheets into
one "pipeline view" — 4–6 hours per week
        │
        ▼
Monthly forecast submitted to CFO
(based on rep estimates, ±40% accuracy)
        │
        ▼
Won: rep sends email to IT, HR, Finance
        │
        ▼ (each reads their email separately)
3 manual tasks triggered — no tracking
```

**Friction points:**
- 7h/rep/week on spreadsheet maintenance
- Lost leads (no follow-up reminders)
- Forecasts based on optimism, not data
- Won deals triggered 3 uncoordinated manual processes

### After State — TO-BE Process (Project 2)

```
Lead captured via web form / LinkedIn → API Hub → QB CRM
        │
        ▼ (seconds)
Auto-scored by Python lead scorer
Auto-assigned to rep with lowest pipeline load
Teams card + email to rep
        │
        ▼
Rep manages deals in Power Apps Kanban board
System tracks all activities via Graph API email sync
Automated daily follow-up digest
        │
        ▼
Stage changes trigger Teams notifications
Won deals trigger onboarding workflow (via Project 6)
        │
        ▼
CFO sees real-time weighted pipeline in Power BI
Forecast accuracy: ±12%
```

---

## Domain 3: Employee Onboarding (Project 3)

### Before State — AS-IS Process

```
HR receives signed offer letter
        │
        ▼ (1–2 days)
HR emails IT: "New starter: John Smith, starts 1 Aug"
        │
        ▼ (IT checks email when available)
IT creates AD account (sometimes Day 1 or later)
        │
        ▼ (separate email to Facilities)
Desk prepared (sometimes)
        │
        ▼ (Day 1: chaos)
New hire arrives, no laptop, no access, no agenda
Manager scrambles
        │
        ▼ (weeks 1–4)
No structured checklist — dependent on manager memory
        │
        ▼ (6 weeks in)
HR check-in: "Are you settled in?" — no data
```

**Measured impact of the before state:**
- 47-day average time-to-productivity (industry benchmark: 28 days)
- 31% had system access on Day 1
- 58% of onboarding checklists "completed" (self-reported, no evidence)
- Two enterprise client relationships strained because their primary contact went 5 weeks without meaningful access

### After State — TO-BE Process (Project 3)

```
HR creates employee record in Quickbase
        │
        ▼ (seconds — automated)
34 tasks created from role template
IT tasks assigned to IT, buddy tasks to buddy, etc.
Azure AD account created (disabled until Day 1)
Welcome email to new hire's personal email
        │
        ▼ (Day 1 morning — 06:00)
AD account enabled automatically
Teams card to manager: "Your new hire starts today"
        │
        ▼
New hire opens Power Apps portal: personalised checklist
Manager has own task list with descriptions
        │
        ▼ (daily 07:00)
Overdue task reminders sent to task owners
        │
        ▼ (milestone by milestone)
Celebration cards at Day 1 / Week 1 / Month 1 / 90 days
```

---

## Domain 4: Procurement (Project 4)

### Before State — AS-IS Process

```
Employee emails manager: "Can I buy a new laptop?"
        │
        ▼ (manager approves via reply email)
Employee emails Finance with quote attached
        │
        ▼ (Finance checks if budget available — manually)
Finance emails CEO for items > R50k
        │
        ▼ (CEO may be traveling)
Approval chain takes 8.3 days average
        │
        ▼ (Finance creates PO in Word template)
3 hours per PO
        │
        ▼
Vendor emailed manually
        │
        ▼ (no tracking)
Delivery: unknown timeline
```

**Key problems:**
- No audit trail (approvals in email threads)
- Budget visibility: zero (Finance discovered overspend in monthly reconcile)
- 6 budget overspend incidents per year (discovered too late)
- PO creation: 3h × ~80 POs/year = 240h Finance overhead/year

### After State — TO-BE Process (Project 4)

```
Employee submits request via Power Apps
        │
        ▼ (real-time)
Python checks budget availability (soft reservation)
Vendor validation check
        │
        ▼ (automatic routing)
Approval chain triggered based on amount threshold
Approvers: approve/reject from email or Teams
No portal login required
        │
        ▼ (all levels approved)
PO auto-generated and emailed to vendor
QB budget committed → spent automatically
ERP sync via API
        │
        ▼
Power BI: finance has real-time spend visibility
```

---

## Domain 5 & 6: Intelligence + Integration (Projects 5 & 6)

### Before State — Intelligence Layer

- CEO received 4 separate Monday-morning emails
- Each formatted differently
- Data from previous Friday (stale)
- No way to see whether IT problems were causing sales problems

### After State — Intelligence Layer

- Single Monday 06:30 HTML report (auto-generated)
- Real-time Power BI dashboard — 15-minute refresh
- Cross-domain correlation analysis (first systemic insight: delayed equipment orders were causing IT SLA breaches which were causing client satisfaction scores to drop)
- Health score: single number with domain breakdown

### Before State — Integration Layer

- 11 separate point-to-point integrations (all manual email)
- ~340 events per month were silently lost
- IT had no visibility into what was flowing where

### After State — Integration Layer

- 1 hub, 11 routes, 94% event success rate
- Every event logged, retried, or dead-lettered
- Non-developers can add routes via Quickbase config table

---

## Stakeholder Map

| Stakeholder | Role | Phase 1 Impact | Phase 2 Impact |
|-------------|------|---------------|---------------|
| CEO | Executive Sponsor | Approved budget, monitored via dashboard | Real-time health score, weekly email |
| COO | Champion (Phase 1) | Service desk transformation owner | Sees ops score on Executive Dashboard |
| CRO | Sales transformation owner | CRM adoption driver | Pipeline visibility in Power BI |
| CHRO | Onboarding transformation | Championed HR platform | Headcount analytics in Power BI |
| CFO | Procurement + Finance | Budget control restored | Spend analytics, ERP sync |
| CTO | Integration oversight | API Hub sponsor | Integration health monitoring |
| IT Manager | Ops delivery lead | Service desk platform owner | Integration hub admin |
| HR Manager | Onboarding delivery | Template design, training | Ongoing administration |
| 3 × Team Leads | Change agents | Trained 40+ staff | Ongoing governance |

---

## Change Management Approach

### Communication Cadence

| Audience | Frequency | Format | Owner |
|----------|-----------|--------|-------|
| Executive team | Weekly | 5-slide deck | Transformation Lead |
| Department heads | Bi-weekly | Teams call | Transformation Lead |
| All staff | Monthly | Email update | CEO (drafted by TL) |
| IT team | Daily (Phase 1) | Standup | IT Manager |

### Training Approach

- **Power Apps portals:** 30-minute role-specific training videos + printed quick reference cards
- **Quickbase admin users:** 4-hour live workshop, 2× follow-up sessions
- **Approvers (Procurement):** 2-minute email with screenshots — no training required
- **New hires:** Self-guided onboarding checklist in their own portal

### Adoption Metrics Tracked

| Platform | Target (Month 3) | Actual (Month 3) | Month 6 |
|----------|-----------------|-----------------|---------|
| Service Desk Power Apps | 80% of tickets via portal | 73% | 91% |
| CRM | 100% of deals in system | 68% | 94% |
| Onboarding checklist completion | 90% | 97% | 97% |
| Procurement portal | 100% of requests via portal | 82% | 98% |
