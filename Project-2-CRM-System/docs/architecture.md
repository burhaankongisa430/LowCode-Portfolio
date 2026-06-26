# Architecture & Data Model

## Quickbase Table Definitions

### Table 1: Contacts (People)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Contact ID | Formula (Text) | "CNT-" & ToText([Record ID#]) |
| 7 | First Name | Text | Required |
| 8 | Last Name | Text | Required |
| 9 | Full Name | Formula (Text) | [First Name] & " " & [Last Name] |
| 10 | Email | Email | Required |
| 11 | Phone | Phone | |
| 12 | Job Title | Text | |
| 13 | Department | Text | |
| 14 | Company | Record Link (Companies) | |
| 15 | Contact Type | Text (multi-choice) | Lead, Prospect, Customer, Partner, Former Customer |
| 16 | Lead Source | Text (multi-choice) | Website, Referral, LinkedIn, Cold Outreach, Event, Marketing, Inbound Call |
| 17 | Lead Score | Numeric | Set by Python scorer |
| 18 | Lead Score Grade | Formula (Text) | A/B/C/D based on score |
| 19 | Owner (Sales Rep) | Record Link (Sales Reps) | |
| 20 | Date Created | Date/Time | Auto |
| 21 | Last Modified | Date/Time | Auto |
| 22 | Last Activity Date | Date/Time | Updated by activity log |
| 23 | Days Since Last Activity | Formula (Numeric) | |
| 24 | LinkedIn URL | URL | |
| 25 | Notes | Text (multiline) | |
| 26 | Do Not Contact | Checkbox | GDPR / opt-out |
| 27 | Open Deals Count | Summary (Deals) | Count of open deals |

---

### Table 2: Companies (Accounts)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Company ID | Formula (Text) | "ACC-" & ToText([Record ID#]) |
| 7 | Company Name | Text | Required |
| 8 | Industry | Text (multi-choice) | Technology, Finance, Healthcare, Retail, Manufacturing, Government, Other |
| 9 | Company Size | Text (multi-choice) | 1–10, 11–50, 51–200, 201–1000, 1000+ |
| 10 | Annual Revenue | Numeric (currency) | |
| 11 | Website | URL | |
| 12 | Country | Text | |
| 13 | City | Text | |
| 14 | Account Owner | Record Link (Sales Reps) | |
| 15 | Account Type | Text (multi-choice) | Prospect, Customer, Partner, Competitor |
| 16 | Date Created | Date/Time | Auto |
| 17 | Total Deal Value | Summary (Deals) | Sum of open deal values |
| 18 | Won Deal Value | Summary (Deals) | Sum of won deal values |
| 19 | Contact Count | Summary (Contacts) | |
| 20 | Notes | Text (multiline) | |

---

### Table 3: Deals (Core Table — Opportunities)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Deal ID | Formula (Text) | "DL-" & ToText([Record ID#]) |
| 7 | Deal Name | Text | Required |
| 8 | Primary Contact | Record Link (Contacts) | |
| 9 | Company | Record Link (Companies) | |
| 10 | Sales Rep | Record Link (Sales Reps) | |
| 11 | Stage | Text (multi-choice) | New Lead, Qualified, Proposal Sent, Negotiation, Verbal Commit, Closed Won, Closed Lost, On Hold |
| 12 | Deal Value | Numeric (currency) | Required |
| 13 | Win Probability % | Formula (Numeric) | Stage-driven |
| 14 | Weighted Value | Formula (Numeric) | Deal Value × Win Probability |
| 15 | Expected Close Date | Date | Required |
| 16 | Actual Close Date | Date | Set on Won/Lost |
| 17 | Lead Source | Text (multi-choice) | Mirrors Contacts.Lead Source |
| 18 | Date Created | Date/Time | Auto |
| 19 | Last Modified | Date/Time | Auto |
| 20 | Last Activity Date | Date/Time | Updated when activity logged |
| 21 | Next Follow-up Date | Date | Set by rep or automation |
| 22 | Days in Stage | Formula (Numeric) | |
| 23 | Days Since Last Activity | Formula (Numeric) | |
| 24 | Deal Age Days | Formula (Numeric) | |
| 25 | Follow-up Status | Formula (Text) | On Time / Due Today / Overdue / No Activity |
| 26 | Days to Close Expected | Formula (Numeric) | |
| 27 | Is Overdue | Formula (Checkbox) | Close date passed and not Won/Lost |
| 28 | Forecast Category | Formula (Text) | Commit / Best Case / Pipeline / Omit |
| 29 | Loss Reason | Text (multi-choice) | Price, Competitor, No Budget, No Decision, Wrong Fit, Timing |
| 30 | Loss Notes | Text (multiline) | |
| 31 | Deal Health Score | Formula (Numeric) | Composite 0–100 |
| 32 | Deal Health Label | Formula (Text) | Healthy / Needs Attention / At Risk / Stalled |
| 33 | Stage Changed Date | Date/Time | Updated by automation on stage change |
| 34 | Previous Stage | Text | Captured by automation |
| 35 | Product Count | Summary (Deal Products) | |
| 36 | Activity Count | Summary (Activities) | |
| 37 | Tags | Text | Comma-separated |
| 38 | Priority | Text (multi-choice) | High, Medium, Low |

---

### Table 4: Pipeline Stages (Reference)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Stage Name | Text | Matches Deals.Stage values |
| 7 | Win Probability % | Numeric | 0–100 |
| 8 | Stage Order | Numeric | 1–8 for sorting |
| 9 | Required Actions | Text (multiline) | What must happen to advance |
| 10 | Max Days Recommended | Numeric | Alert if deal exceeds this in stage |
| 11 | Is Closed Stage | Checkbox | Won or Lost |
| 12 | Stage Color | Text | Hex code for UI |

**Seed data:**

| Stage | Win % | Order | Max Days |
|-------|-------|-------|----------|
| New Lead | 5 | 1 | 3 |
| Qualified | 20 | 2 | 7 |
| Proposal Sent | 40 | 3 | 14 |
| Negotiation | 70 | 4 | 21 |
| Verbal Commit | 85 | 5 | 10 |
| Closed Won | 100 | 6 | — |
| Closed Lost | 0 | 7 | — |
| On Hold | — | 8 | — |

---

### Table 5: Activities (Interaction Log)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Activity ID | Formula (Text) | "ACT-" & ToText([Record ID#]) |
| 7 | Deal | Record Link (Deals) | |
| 8 | Contact | Record Link (Contacts) | |
| 9 | Activity Type | Text (multi-choice) | Email Sent, Email Received, Call, Meeting, Demo, Proposal, LinkedIn, Note, Task, Stage Change |
| 10 | Subject | Text | |
| 11 | Notes | Text (multiline) | |
| 12 | Activity Date | Date/Time | |
| 13 | Duration Minutes | Numeric | For calls / meetings |
| 14 | Outcome | Text (multi-choice) | Positive, Neutral, Negative, No Response |
| 15 | Logged By | Text | Rep name or "System" |
| 16 | Logged By Email | Email | |
| 17 | Source | Text | Manual, Graph API, Automation |
| 18 | Follow-up Required | Checkbox | |
| 19 | Follow-up Date | Date | |
| 20 | Date Created | Date/Time | Auto |

---

### Table 6: Products / Services

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Product Code | Text | SKU / code |
| 7 | Product Name | Text | Required |
| 8 | Category | Text (multi-choice) | Software, Hardware, Service, License, Support |
| 9 | Unit Price | Numeric (currency) | List price |
| 10 | Description | Text (multiline) | |
| 11 | Is Active | Checkbox | |

---

### Table 7: Deal Products (Junction — many-to-many)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Deal | Record Link (Deals) | |
| 7 | Product | Record Link (Products) | |
| 8 | Quantity | Numeric | |
| 9 | Unit Price | Numeric (currency) | Can override list price |
| 10 | Discount % | Numeric | |
| 11 | Line Total | Formula (Numeric) | Qty × Unit Price × (1 - Discount/100) |

---

### Table 8: Sales Reps

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Rep Name | Text | |
| 7 | Email | Email | |
| 8 | Team | Text | |
| 9 | Manager | Record Link (Sales Reps) | Self-referential |
| 10 | Quota (Monthly) | Numeric (currency) | |
| 11 | Is Active | Checkbox | |
| 12 | Open Pipeline Value | Summary (Deals) | Sum of weighted deal values |
| 13 | Won This Month | Summary (Deals) | Sum of won deals current month |
| 14 | Quota Attainment % | Formula (Numeric) | Won / Quota × 100 |

---

## Table Relationships

```
Companies (1) ──────────────── (many) Contacts
Companies (1) ──────────────── (many) Deals
Contacts (1) ───────────────── (many) Deals   [Primary Contact]
Sales Reps (1) ─────────────── (many) Deals
Sales Reps (1) ─────────────── (many) Contacts
Deals (1) ──────────────────── (many) Activities
Contacts (1) ───────────────── (many) Activities
Deals (1) ──────────────────── (many) Deal Products
Products (1) ───────────────── (many) Deal Products
Pipeline Stages ──── (reference lookup, not a hard link)
```

---

## Role-Based Permissions

| Role | Contacts | Companies | Deals | Activities | Products | Reps Table | Reports |
|------|----------|-----------|-------|------------|----------|-----------|---------|
| Sales Rep | Own + Team | View | Own only | Own only | View | View self | Own pipeline |
| Team Lead | Team | View + Edit | Team | Team | View | View team | Team dashboard |
| Sales Manager | Full | Full | Full | Full | Edit | Full | Full |
| Admin | Full | Full | Full | Full | Full | Full | Full |
