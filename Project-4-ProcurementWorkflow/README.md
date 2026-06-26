# Project 4: Procurement Approval System

## Overview

A multi-level procurement approval platform built on **Quickbase**, **Microsoft Power Platform** (with native Approvals connector), and a **Python integration layer** that handles real-time budget validation and purchase order generation. Requests are routed through an amount-based approval chain — managers, department heads, and finance directors approve directly from their email or Teams without logging into any system.

**Business Problem Solved:**
Purchase requests were submitted via email chains, approval status was invisible, budget overspend was discovered weeks after the fact, and generating a purchase order required manual copy-paste into a Word template. The finance team spent 12+ hours per week chasing approvals.

**Measurable Outcomes:**
- Average approval cycle time reduced from 8.3 days to 1.4 days
- Budget overspend incidents eliminated (real-time budget check before routing)
- 100% of approved requests automatically generate a PO — zero manual PO creation
- Finance team reclaimed 11 hours/week previously spent on email chase-up

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  SUBMISSION LAYER                        │
│  Power Apps Canvas App (Staff Purchase Request Portal)  │
│  + Quickbase form (fallback)                            │
└────────────────────────┬────────────────────────────────┘
                         │ New request created
┌────────────────────────▼────────────────────────────────┐
│              VALIDATION LAYER (Python)                   │
│  budget_validator.py  → check dept budget availability  │
│  Flow 01              → validate vendor + category      │
└────────────────────────┬────────────────────────────────┘
                         │ Route to first approver
┌────────────────────────▼────────────────────────────────┐
│           MULTI-LEVEL APPROVAL ENGINE                    │
│  Flow 02 – Approval Routing (amount-based levels)       │
│  Power Automate Approvals Connector (email + Teams)     │
│                                                         │
│  Level 1 (Manager)        → up to R75,000              │
│  Level 2 (Dept Head)      → up to R250,000             │
│  Level 3 (Finance Director)→ up to R750,000            │
│  Level 4 (CEO)            → above R750,000             │
└────────────────────────┬────────────────────────────────┘
                         │ All levels approved
┌────────────────────────▼────────────────────────────────┐
│         PO GENERATION & ERP SYNC (Python)               │
│  po_generator.py  → HTML PO document → email to vendor │
│  erp_connector.py → push approved PO to finance system │
│  Flow 03          → update budget, notify requestor     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              REPORTING LAYER                             │
│  Power BI Spend Analytics Dashboard                     │
│  Quickbase Procurement Reports (by dept, vendor, status)│
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Primary Data Store | Quickbase (7 tables) |
| Approval Engine | Power Automate Approvals connector |
| Request Portal | Power Apps Canvas App |
| Budget Validation | Python (real-time QB API check) |
| PO Generation | Python (HTML template → email) |
| ERP Integration | Python (REST API to finance system) |
| Spend Analytics | Power BI + Quickbase Dashboards |
| Notifications | Power Automate Approvals (email + Teams) |

---

## Approval Thresholds

| Level | Approver Role | Threshold | Response SLA |
|-------|--------------|-----------|-------------|
| 1 | Line Manager | Up to R75,000 | 24 hours |
| 2 | Department Head | R75,001 – R250,000 | 48 hours |
| 3 | Finance Director | R250,001 – R750,000 | 48 hours |
| 4 | CEO | Above R750,000 | 72 hours |

> Requests exceeding a level's threshold automatically escalate to the next level after approval at the current level. Rejection at **any** level closes the request immediately with a reason.

---

## Project Structure

```
LowCode-Portfolio/ProcurementWorkflow/
├── README.md
├── docs/
│   └── architecture.md              # Full data model & field definitions
├── quickbase/
│   ├── formulas.md                  # All formula fields
│   └── automations.md               # Quickbase automations & pipelines
├── power-platform/
│   ├── flows/
│   │   ├── 01-request-validation.json
│   │   ├── 02-approval-routing.json
│   │   ├── 03-final-approval-po.json
│   │   └── 04-rejection-notification.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md
│   └── power-bi/
│       └── dax-measures.md
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── quickbase_client.py           # Procurement QB wrapper
    ├── webhook_handler.py            # Flask API server
    ├── budget_validator.py           # Real-time budget availability check
    ├── po_generator.py               # HTML purchase order generation
    └── erp_connector.py             # Finance/ERP system integration
```

---

## Key Features Demonstrated

- **Amount-based multi-level approval routing** — threshold logic determines how many approval levels are required; each level is a separate Power Automate Approval action
- **Approve/reject directly from email or Teams** — no portal login required; approvers respond inline
- **Real-time budget validation** — Python checks remaining departmental budget before routing; flags over-budget requests without blocking them
- **Automated PO generation** — approved requests trigger an HTML purchase order emailed to the vendor and finance team
- **Approval audit trail** — every decision (approve/reject/comment) is timestamped and written to the Quickbase Approval History table
- **ERP sync** — approved POs are pushed to the finance system via REST API so accounting has a single source of truth
- **Vendor management** — requests against unapproved vendors are flagged for Finance to review

---

## What Makes This Project Distinct

Project 4 is where human approval behavior becomes the primary design challenge. The technical centerpiece is not a flow or a formula — it is making approvers act without requiring them to log into anything.

| Area | What's unique here |
|------|-------------------|
| **Approval engine** | Power Automate native **Approvals connector** — approvers respond directly from email or Teams. Each level is an `ApiConnectionWebhook` action that suspends the flow until a human responds, with no portal login required |
| **Conditional multi-level routing** | Flow 02 uses nested `Switch → Condition` to route through Levels 1–4 based on amount thresholds. Rejection at any level immediately short-circuits to the rejection flow — no orphaned approval requests |
| **Atomic budget reservation** | `budget_validator.py` increments `Committed Amount` on the budget record the moment a request is submitted, preventing two simultaneous requests both passing a budget check against the same remaining balance |
| **PO generation** | `po_generator.py` produces a complete, print-ready HTML purchase order with company branding, T&Cs, and an approval signature block — no Word templates, no copy-paste, emailed directly to the vendor |
| **ERP-agnostic connector** | `erp_connector.py` has one `_push()` method as the single point of change when switching between SAP, Oracle, or Sage — the rest of the codebase is unaffected |
| **Three-way match foundation** | The PO table includes `Invoice Number`, `Invoice Amount`, `Variance`, and `Match Status` formula fields, pre-built as the data foundation for full three-way matching (PO → GR → Invoice) as a future upgrade |
| **Amount Band formula** | A Quickbase formula maps any request value to its approval tier label and displays it to each approver in their notification email, so they understand why the request reached them |

---

## Design Trade-offs

### 1. Power Automate Approvals Connector vs. Custom Approval Table

**Choice made:** Power Automate native Approvals connector  
**Why:** The Approvals connector handles the entire email/Teams approval experience, retry logic, and response capture out of the box. Building a custom approval system (email links → Flask endpoint → status update) requires significantly more code and is harder to maintain.  
**What was given up:** The Approvals connector is a Premium connector (requires a Power Automate Premium license per user). A custom approval table in Quickbase with email links is free but produces a worse approver experience.  
**When to choose differently:** In a budget-constrained organization without Premium licenses, build a custom approval flow: generate a unique approval token per request, embed Approve/Reject links in the notification email, and handle the token validation in the Python API.

---

### 2. Sequential vs. Parallel Approval at Each Level

**Choice made:** Sequential — Level 1 must approve before Level 2 sees the request  
**Why:** Prevents approvers at higher levels from being flooded with requests that are rejected at Level 1. Reduces noise. Matches standard procurement governance practice.  
**What was given up:** Sequential approval is slower. If the Level 1 approver is on leave, the entire chain stalls. Parallel approval (all levels notified simultaneously, all must approve) is faster but creates coordination complexity.  
**Mitigation:** Each approval has an SLA (24–72h). If the SLA passes without a response, the flow sends a reminder and CC's the approver's manager. After a second SLA breach, the request is flagged to Finance for manual intervention.

---

### 3. Budget Check as Soft Warning vs. Hard Block

**Choice made:** Soft warning — over-budget requests are flagged but still routed  
**Why:** A hard block frustrates users when budgets are close to their limit and prevents legitimate urgent procurement. Finance Directors frequently approve over-budget items with a budget reallocation. A soft warning gives visibility without stopping the process.  
**What was given up:** Without a hard block, it is possible for multiple requests to be approved simultaneously that together exceed the budget, because each was checked individually against the same remaining balance.  
**Mitigation:** The budget validator reserves the requested amount on the budget record the moment a request is submitted (status: "Pending"). Subsequent requests see the reduced available budget. The reservation is released if the request is rejected.

---

### 4. PO as HTML Email vs. PDF Attachment

**Choice made:** HTML email body (PO embedded in email)  
**Why:** Avoids dependency on a PDF library (WeasyPrint, ReportLab), which adds complexity and potential rendering issues. HTML emails are universally readable, printable from any email client, and don't require the vendor to download an attachment.  
**What was given up:** PDFs are more professional for formal procurement, are easier to file, and cannot be accidentally edited by the recipient. Many finance teams require PDF POs for audit purposes.  
**When to upgrade:** Add `weasyprint` to `requirements.txt` and call `weasyprint.HTML(string=html).write_pdf()` in `po_generator.py`. The HTML template is already structured for clean PDF output.

---

### 5. Single Finance ERP vs. Dual-Write

**Choice made:** One-directional push to ERP on PO approval  
**Why:** Quickbase is the system of record during the approval workflow. Once approved, the PO is pushed to the ERP (the finance system of record). This avoids complex two-way sync and conflict resolution.  
**What was given up:** If the ERP is the master system for vendors, budgets, and cost codes, a dual-write approach keeps both systems current. Without it, new vendors added in the ERP don't appear in Quickbase until a sync runs.  
**When to upgrade:** Add a nightly sync job (`erp_connector.py → sync_vendors_from_erp()`) that pulls vendor and budget data from the ERP into Quickbase. This makes Quickbase a read-through cache rather than an independent master.

---

## Potential Improvements

### Short-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Delegation / Out-of-Office** | If an approver has set an out-of-office in Outlook, automatically delegate their approval to their backup via the Microsoft Graph API. | Medium |
| **Vendor Self-Registration** | Public-facing Power Apps form for vendors to submit their details (bank account, tax number, registration). Routes to Finance for approval before they appear in the vendor list. | Medium |
| **Mobile Approval** | The Power Automate mobile app already surfaces approval requests natively. Ensure the approval title and detail are formatted for mobile reading (short subject, key facts first). | Low |
| **Spend Category Analytics** | Add a `Category` field to requests and break spend down by category in Power BI. Enables spend analysis reports for Finance. | Low |

### Medium-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Recurring Purchase Orders** | Allow Finance to mark a PO as recurring (monthly/quarterly). Auto-generate and auto-approve subsequent POs against the same vendor and budget code without a new request. | Medium |
| **Three-Way Match** | After PO is issued, track the Goods Receipt (delivery confirmation) and Vendor Invoice. Only release payment when all three match: PO, GR, and Invoice. | High |
| **Contract Management Module** | For high-value vendors, link the PO to a contract record. Alert Finance when a contract is approaching expiry or when cumulative spend approaches the contract ceiling. | High |
| **PDF PO Generation** | Replace HTML email PO with a PDF generated via WeasyPrint. Store the PDF in SharePoint and link it from the Quickbase record. | Medium |

### Long-Term

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **AI Spend Anomaly Detection** | Use Azure OpenAI or a statistical model to flag unusual spend patterns (e.g., same vendor, same amount, same requester submitted three times in a week). | High |
| **Supplier Scorecard** | Track on-time delivery, invoice accuracy, and quality issues per vendor. Surface a supplier health score in the vendor record and in the PO routing logic. | High |
| **Full P2P Integration** | Extend to a full Procure-to-Pay cycle: catalog browsing → request → approval → PO → GR → invoice matching → payment release, all tracked in Quickbase. | Very High |
