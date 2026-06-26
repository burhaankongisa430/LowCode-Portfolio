# Quickbase Automations

---

## Automation 1: Request Submitted — Trigger Validation Flow

**Trigger:** Record Changed in **Purchase Requests**  
**Condition:** `[Status] = "Submitted"` AND `[Status (previous value)] = "Draft"`

### Actions:
1. **Update Record** — Committed Amount on Budget Code: increase by `[Total Amount]`
2. **Send Webhook** to Python `/api/procurement/validate`
   ```json
   {
     "requestRecordId": "{{[Record ID#]}}",
     "requestNumber":   "{{[Request Number]}}",
     "title":           "{{[Title]}}",
     "totalAmount":     {{[Total Amount]}},
     "departmentId":    "{{[Department - Record ID#]}}",
     "budgetCode":      "{{[Budget Code]}}",
     "vendorId":        "{{[Vendor - Record ID#]}}",
     "vendorName":      "{{[Vendor - Vendor Name]}}",
     "category":        "{{[Category]}}",
     "requestorName":   "{{[Requestor Name]}}",
     "requestorEmail":  "{{[Requestor Email]}}",
     "managerEmail":    "{{[Manager Approver Email]}}",
     "isUrgent":        {{[Is Urgent]}}
   }
   ```
   Python validates vendor + budget, returns `{"budgetWarning": bool, "vendorWarning": bool}`

3. **Send Webhook** to Power Automate validation + routing flow

---

## Automation 2: Status Changed — Log to Approval History

**Trigger:** Record Changed in **Purchase Requests**  
**Condition:** `[Status] != [Status (previous value)]`

### Actions:
1. **Create Record in Approval History**
   - Purchase Request: `[Record ID#]`
   - Decision: `"Status Change"`
   - Comments: `"Status changed from " & [Status (previous value)] & " to " & [Status]`
   - Decision Date: `Now()`
   - Approval Method: `"System"`

---

## Automation 3: Request Rejected — Release Budget Commitment

**Trigger:** Record Changed in **Purchase Requests**  
**Condition:** `[Status] = "Rejected"` AND `[Status (previous value)] != "Rejected"`

### Actions:
1. **Update Related Record in Budget Codes**
   - Committed Amount: decrease by `[Total Amount]`
   *(Committed is reserved at submission; if rejected, it is released)*

2. **Send Email**
   - To: `[Requestor Email]`
   - Subject: `"Purchase Request " & [Request Number] & " – Rejected"`
   - Body includes: rejection reason, rejected by, next steps

---

## Automation 4: PO Issued — Update Budget Spent and Release Commitment

**Trigger:** Record Changed in **Purchase Requests**  
**Condition:** `[Status] = "PO Issued"` AND `[Status (previous value)] != "PO Issued"`

### Actions:
1. **Update Related Record in Budget Codes**
   - Committed Amount: decrease by `[Total Amount]`  
   - Spent Amount: increase by `[Total Amount]`

---

## Automation 5: SLA Breach Alert (Scheduled)

**Trigger:** Scheduled — Every 6 hours  
**Condition:** `[SLA Breached] = true`

### Actions:
1. **Send Email**
   - To: `finance@yourcompany.com`
   - Subject: `"Approval SLA Breached: " & [Request Number]`
   - Body: request details, current approval level, days waiting

---

## Automation 6: Budget Alert — High Utilization

**Trigger:** Record Changed in **Budget Codes**  
**Condition:** `[Utilization %] >= [Budget Alert Threshold %]` AND `[Budget Status] != "Overspent"`

### Actions:
1. **Send Email**
   - To: `[Department Head Email]`; CC: `[Finance Director Email]`
   - Subject: `[Department Name] & " budget at " & ToText([Utilization %]) & "%"`
   - Body: budget summary table with committed, spent, and available amounts

---

## Pipeline: Sync Approved PO to ERP

**Quickbase Pipeline** — triggered when a Purchase Order record is created

```json
{
  "name": "Sync PO to ERP",
  "steps": [
    {
      "type": "trigger",
      "source": "record_created",
      "table": "{{PURCHASE_ORDERS_TABLE_ID}}"
    },
    {
      "type": "action",
      "app": "http",
      "method": "POST",
      "url": "https://your-api-server/api/procurement/erp-sync",
      "body": {
        "poNumber":       "{{6}}",
        "requestNumber":  "{{7.value.6}}",
        "vendorName":     "{{8.value.7}}",
        "vendorEmail":    "{{8.value.9}}",
        "amount":         "{{12}}",
        "currency":       "{{13}}",
        "budgetCode":     "{{11}}",
        "department":     "{{10}}",
        "paymentTerms":   "{{14}}",
        "issueDate":      "{{16}}"
      }
    }
  ]
}
```
