# Architecture & Data Model

## Quickbase Table Definitions

### Table 1: Purchase Requests (Core)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Request Number | Formula (Text) | "PR-" & Right("0000" & ToText([Record ID#]), 5) |
| 7 | Title | Text | Required — brief description of what is being purchased |
| 8 | Description | Text (multiline) | Full justification |
| 9 | Requestor Name | Text | Required |
| 10 | Requestor Email | Email | Required |
| 11 | Department | Record Link (Budget Codes) | Required |
| 12 | Budget Code | Text | GL / cost center code |
| 13 | Vendor | Record Link (Vendors) | |
| 14 | Vendor Name (override) | Text | If vendor not in approved list |
| 15 | Category | Text (multi-choice) | IT Equipment, Software/SaaS, Office Supplies, Marketing, Professional Services, Facilities, Travel, Other |
| 16 | Total Amount | Numeric (currency) | Required |
| 17 | Currency | Text (multi-choice) | ZAR, USD, EUR, GBP — default ZAR |
| 18 | Required By Date | Date | |
| 19 | Status | Text (multi-choice) | Draft, Submitted, Under Review, Level 1 Pending, Level 2 Pending, Level 3 Pending, Level 4 Pending, Approved, Rejected, PO Issued, Canceled |
| 20 | Approval Level Required | Formula (Numeric) | Based on amount thresholds |
| 21 | Current Approval Level | Numeric | Updated by flow |
| 22 | Manager Approver | Text | Level 1 approver name |
| 23 | Manager Approver Email | Email | |
| 24 | Dept Head Approver | Text | Level 2 |
| 25 | Dept Head Email | Email | |
| 26 | Finance Director Email | Email | Level 3 |
| 27 | CEO Email | Email | Level 4 |
| 28 | Rejected By | Text | |
| 29 | Rejection Reason | Text (multiline) | |
| 30 | Approved By | Text | Final approver name |
| 31 | Approval Date | Date/Time | |
| 32 | PO Number | Text | Set when PO is generated |
| 33 | PO Issued Date | Date | |
| 34 | Budget Available | Numeric (currency) | Snapshot at submission |
| 35 | Budget Warning | Checkbox | True if request > available budget |
| 36 | Is Urgent | Checkbox | Flags for expedited review |
| 37 | Attachments | File Attachment | Quotes, specifications |
| 38 | Notes | Text (multiline) | Internal notes |
| 39 | Date Created | Date/Time | Auto |
| 40 | Date Modified | Date/Time | Auto |
| 41 | Vendor Approved | Formula (Checkbox) | Is vendor in approved list? |
| 42 | Days in Current Status | Formula (Numeric) | |
| 43 | SLA Breached | Formula (Checkbox) | Approval overdue |
| 44 | Amount Band | Formula (Text) | Under R75k / R75k–R250k / etc. |

---

### Table 2: Vendors (Approved Supplier List)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Vendor Code | Formula (Text) | "VND-" & ToText([Record ID#]) |
| 7 | Vendor Name | Text | Required |
| 8 | Contact Name | Text | |
| 9 | Contact Email | Email | Used for PO delivery |
| 10 | Contact Phone | Phone | |
| 11 | Category | Text (multi-choice) | What the vendor supplies |
| 12 | Status | Text (multi-choice) | Approved, Pending Review, Suspended, Blacklisted |
| 13 | Country | Text | |
| 14 | Bank Account | Text | Encrypted/masked |
| 15 | Tax Number | Text | VAT / PAYE registration |
| 16 | Company Reg Number | Text | |
| 17 | Payment Terms | Text (multi-choice) | Net 30, Net 60, EOM, COD |
| 18 | Preferred Currency | Text (multi-choice) | ZAR, USD, EUR, GBP |
| 19 | Date Added | Date | |
| 20 | Added By | Text | |
| 21 | Last PO Date | Summary (Requests) | Most recent PO issued date |
| 22 | Total PO Value (YTD) | Summary (Requests) | Sum of approved POs this year |
| 23 | Notes | Text (multiline) | |

---

### Table 3: Budget Codes (Departmental Budgets)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Budget Code | Text | GL code / cost center |
| 7 | Department Name | Text | |
| 8 | Department Head | Text | |
| 9 | Department Head Email | Email | Level 2 approver |
| 10 | Annual Budget | Numeric (currency) | Total approved budget |
| 11 | Committed Amount | Numeric (currency) | Sum of pending + approved requests |
| 12 | Spent Amount | Numeric (currency) | Sum of PO-issued requests |
| 13 | Available Budget | Formula (Numeric) | Annual − Committed − Spent |
| 14 | Utilization % | Formula (Numeric) | (Committed + Spent) / Annual × 100 |
| 15 | Budget Year | Text | e.g., "2026" |
| 16 | Is Active | Checkbox | |
| 17 | Budget Alert Threshold % | Numeric | Default 85 — alert when utilization exceeds this |
| 18 | Budget Status | Formula (Text) | Healthy / At Risk / Overspent |
| 19 | Finance Director | Text | Level 3 approver for this dept |
| 20 | Finance Director Email | Email | |

---

### Table 4: Approval History (Audit Trail)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Purchase Request | Record Link (Requests) | |
| 7 | Approval Level | Numeric | 1–4 |
| 8 | Approver Name | Text | |
| 9 | Approver Email | Email | |
| 10 | Decision | Text (multi-choice) | Approved, Rejected, Delegated, Escalated |
| 11 | Comments | Text (multiline) | |
| 12 | Decision Date | Date/Time | |
| 13 | Response Time Hours | Numeric | Time from request sent to decision |
| 14 | Sent Date | Date/Time | When the approval request was sent |
| 15 | Approval Method | Text | Email, Teams, Portal |

---

### Table 5: Purchase Orders

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | PO Number | Formula (Text) | "PO-" & Right("00000" & ToText([Record ID#]), 6) |
| 7 | Purchase Request | Record Link (Requests) | |
| 8 | Vendor | Record Link (Vendors) | |
| 9 | Requestor Name | Text | |
| 10 | Department | Text | |
| 11 | Budget Code | Text | |
| 12 | PO Amount | Numeric (currency) | |
| 13 | Currency | Text | |
| 14 | Payment Terms | Text | From vendor record |
| 15 | Delivery Address | Text (multiline) | |
| 16 | Issue Date | Date | |
| 17 | Expected Delivery Date | Date | From original request |
| 18 | Status | Text (multi-choice) | Issued, Acknowledged, Goods Received, Invoiced, Paid, Canceled |
| 19 | Invoice Number | Text | Set when invoice received |
| 20 | Invoice Amount | Numeric (currency) | |
| 21 | Invoice Date | Date | |
| 22 | Variance | Formula (Numeric) | PO Amount − Invoice Amount |
| 23 | ERP Reference | Text | ID in the finance/ERP system |
| 24 | PO HTML | Text (multiline) | Generated PO document |
| 25 | Date Created | Date/Time | Auto |

---

### Table 6: Approvers (Configuration)

| Field # | Field Name | Type | Notes |
|---------|-----------|------|-------|
| 3 | Record ID | Record ID | Auto |
| 6 | Approver Name | Text | |
| 7 | Approver Email | Email | |
| 8 | Role | Text (multi-choice) | Manager, Department Head, Finance Director, CEO |
| 9 | Department | Text | Which dept this person approves for |
| 10 | Max Approval Amount | Numeric (currency) | Upper limit for this approver |
| 11 | Delegate Name | Text | Out-of-office delegate |
| 12 | Delegate Email | Email | |
| 13 | Is Active | Checkbox | |

---

## Approval Routing Logic

```
Request Submitted
       │
       ▼
Budget Check → flag if over-budget (soft warning, does not block)
       │
       ▼
Level 1: Line Manager (always required)
  ├── Rejected → Close request, notify requestor
  └── Approved
         │
         ├── Amount ≤ R75,000 → APPROVED → Generate PO
         │
         └── Amount > R75,000 → Level 2: Department Head
               ├── Rejected → Close request
               └── Approved
                     │
                     ├── Amount ≤ R250,000 → APPROVED → Generate PO
                     │
                     └── Amount > R250,000 → Level 3: Finance Director
                           ├── Rejected → Close request
                           └── Approved
                                 │
                                 ├── Amount ≤ R750,000 → APPROVED → Generate PO
                                 │
                                 └── Amount > R750,000 → Level 4: CEO
                                       ├── Rejected → Close request
                                       └── Approved → Generate PO
```

## Table Relationships

```
Budget Codes (1) ──── (many) Purchase Requests
Vendors (1) ─────── (many) Purchase Requests
Purchase Requests (1) ─ (many) Approval History
Purchase Requests (1) ─ (1)   Purchase Orders
Approvers ─── (configuration — not hard-linked, looked up by dept + role)
```
