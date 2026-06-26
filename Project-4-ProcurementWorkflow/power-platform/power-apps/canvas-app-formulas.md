# Power Apps Canvas App — Power Fx Formulas

Three role-based views: Staff request portal, Finance admin console, Approver summary.

---

## App OnStart

```powerfx
Set(
    gblCurrentUser,
    {
        email:     User().Email,
        name:      User().FullName,
        isFinance: User().Email in ["finance-lead@company.com", "cfo@company.com"],
        isApprover:!IsBlank(LookUp(Approvers, 'Approver Email' = User().Email && 'Is Active'))
    }
);

// Load reference data
ClearCollect(colCategories,
    ["IT Equipment","Software/SaaS","Office Supplies","Marketing",
     "Professional Services","Facilities","Travel","Other"]);

ClearCollect(colCurrencies, ["ZAR","USD","EUR","GBP"]);

ClearCollect(colApprovalThresholds,
    Table(
        {Level: 1, Label: "Manager",          MaxAmount: 75000,   Color: "#E67E22"},
        {Level: 2, Label: "Department Head",   MaxAmount: 250000,  Color: "#D35400"},
        {Level: 3, Label: "Finance Director",  MaxAmount: 750000,  Color: "#C0392B"},
        {Level: 4, Label: "CEO",               MaxAmount: 9999999, Color: "#922B21"}
    )
);

Navigate(
    If(gblCurrentUser.isFinance, scrFinanceConsole,
       If(gblCurrentUser.isApprover, scrApproverView, scrRequestPortal)),
    ScreenTransition.Fade
)
```

---

## Screen: Request Portal (scrRequestPortal)

### My Requests Gallery — Items
```powerfx
SortByColumns(
    Filter(
        'Purchase Requests',
        'Requestor Email' = gblCurrentUser.email
    ),
    "Date Created",
    SortOrder.Descending
)
```

### Status Badge Fill
```powerfx
ColorValue(ThisItem.'Status Color')
```

### Approval Level Indicator — Text
```powerfx
If(
    ThisItem.Status in ["Level 1 Pending","Level 2 Pending","Level 3 Pending","Level 4 Pending"],
    "Awaiting Level " & ThisItem.'Current Approval Level' & " approval",
    ThisItem.Status
)
```

### SLA Breach Warning — Visible
```powerfx
ThisItem.'SLA Breached' = true
```

### New Request Form — OnSubmit validation
```powerfx
If(
    IsBlank(txtTitle.Text) ||
    IsBlank(txtAmount.Text) ||
    IsBlank(drpCategory.Selected.Value) ||
    IsBlank(drpVendor.Selected.'Record ID') ||
    IsBlank(drpBudgetCode.Selected.'Record ID'),

    Notify("Please complete all required fields.", NotificationType.Warning),

    // Validate amount is numeric
    If(
        !IsNumeric(txtAmount.Text) || Value(txtAmount.Text) <= 0,
        Notify("Please enter a valid amount greater than zero.", NotificationType.Warning),

        // Show approval path preview before submitting
        Set(
            gblApprovalPreview,
            LookUp(
                colApprovalThresholds,
                Value(txtAmount.Text) <= MaxAmount
            )
        );
        Set(gblShowConfirm, true)
    )
)
```

### Approval Path Preview Label — Text
```powerfx
"This request (R" &
Text(Value(txtAmount.Text), "#,##0") &
") will require approval from: " &
Concat(
    Filter(
        colApprovalThresholds,
        Level <= If(Value(txtAmount.Text) > 750000, 4,
                    If(Value(txtAmount.Text) > 250000, 3,
                        If(Value(txtAmount.Text) > 75000, 2, 1)))
    ),
    Label & " → ",
    Level
)
```

### Confirm Submit Button — OnSelect
```powerfx
// Create request as Draft first
Set(gblNewRequest,
    Patch(
        'Purchase Requests',
        Defaults('Purchase Requests'),
        {
            Title:             txtTitle.Text,
            Description:       txtDescription.Text,
            'Requestor Name':  gblCurrentUser.name,
            'Requestor Email': gblCurrentUser.email,
            Department:        {Id: drpBudgetCode.Selected.'Record ID'},
            'Budget Code':     drpBudgetCode.Selected.'Budget Code',
            Vendor:            {Id: drpVendor.Selected.'Record ID'},
            Category:          drpCategory.Selected.Value,
            'Total Amount':    Value(txtAmount.Text),
            Currency:          drpCurrency.Selected.Value,
            'Required By Date':datRequiredBy.SelectedDate,
            'Is Urgent':       togUrgent.Value,
            Status:            "Draft"
        }
    )
);

// Immediately submit
Patch(
    'Purchase Requests',
    gblNewRequest,
    {Status: "Submitted"}
);

Set(gblShowConfirm, false);
Notify(
    "✅ Request " & gblNewRequest.'Request Number' & " submitted for approval.",
    NotificationType.Success
);
Navigate(scrRequestPortal, ScreenTransition.Back)
```

### Budget Available Preview — Text (shows remaining budget for selected dept)
```powerfx
If(
    IsBlank(drpBudgetCode.Selected.'Record ID'),
    "Select a budget code to see available balance",
    "Available: R" &
    Text(drpBudgetCode.Selected.'Available Budget', "#,##0") &
    " of R" & Text(drpBudgetCode.Selected.'Annual Budget', "#,##0") &
    " (" & Text(100 - drpBudgetCode.Selected.'Utilization %', "0.0") & "% remaining)"
)
```

### Budget Warning Visible
```powerfx
!IsBlank(drpBudgetCode.Selected.'Record ID') &&
Value(txtAmount.Text) > drpBudgetCode.Selected.'Available Budget'
```

---

## Screen: Finance Admin Console (scrFinanceConsole)

### All Requests Gallery — Items
```powerfx
Filter(
    'Purchase Requests',
    (drpStatusFilter.Selected.Value = "All" || Status = drpStatusFilter.Selected.Value) &&
    (drpDeptFilter.Selected.Value = "All" || 'Department - Department Name' = drpDeptFilter.Selected.Value) &&
    (IsBlank(txtSearch.Text) || 'Request Number' in txtSearch.Text || Title in txtSearch.Text)
)
```

### KPI: Pending Approvals
```powerfx
CountIf(
    'Purchase Requests',
    Status in ["Level 1 Pending","Level 2 Pending","Level 3 Pending","Level 4 Pending"]
)
```

### KPI: Total Committed (Month)
```powerfx
Text(
    Sum(
        Filter(
            'Purchase Requests',
            Status <> "Rejected" && Status <> "Canceled" &&
            Month('Date Created') = Month(Today()) &&
            Year('Date Created') = Year(Today())
        ),
        'Total Amount'
    ),
    "R #,##0"
)
```

### KPI: SLA Breaches
```powerfx
CountIf('Purchase Requests', 'SLA Breached' = true)
```

### Budget Utilization Gallery — Items
```powerfx
Sort('Budget Codes', 'Utilization %', SortOrder.Descending)
```

### Budget Bar Width
```powerfx
(ThisItem.'Utilization %' / 100) * (Parent.Width - 16)
```

### Budget Bar Fill
```powerfx
ColorValue(ThisItem.'Budget Status Color')
```

### Approve Pending Vendor Button — OnSelect (finance can directly approve unapproved vendor)
```powerfx
Patch(
    Vendors,
    LookUp(Vendors, 'Record ID' = galRequests.Selected.Vendor.'Record ID'),
    {Status: "Approved"}
);
Notify("Vendor approved.", NotificationType.Success)
```

---

## Screen: Approver View (scrApproverView)

### Pending Approvals for This Approver — Items
```powerfx
Filter(
    'Purchase Requests',
    (
        (Status = "Level 1 Pending" && 'Manager Approver Email' = gblCurrentUser.email) ||
        (Status = "Level 2 Pending" && 'Dept Head Email' = gblCurrentUser.email) ||
        (Status = "Level 3 Pending" && 'Finance Director Email' = gblCurrentUser.email) ||
        (Status = "Level 4 Pending" && 'CEO Email' = gblCurrentUser.email)
    )
)
```

### Approve Button — OnSelect
```powerfx
// Record approval via Power Automate flow
Set(
    gblApproveResult,
    ProcApprovalFlow.Run(
        galApproverQueue.Selected.'Record ID',
        "Approve",
        txtApproverComment.Text,
        gblCurrentUser.name,
        gblCurrentUser.email
    )
);
Notify("Approved: " & galApproverQueue.Selected.'Request Number', NotificationType.Success);
Refresh('Purchase Requests')
```

### Reject Button — OnSelect
```powerfx
If(
    IsBlank(txtApproverComment.Text),
    Notify("A rejection reason is required.", NotificationType.Warning),

    Set(
        gblRejectResult,
        ProcApprovalFlow.Run(
            galApproverQueue.Selected.'Record ID',
            "Reject",
            txtApproverComment.Text,
            gblCurrentUser.name,
            gblCurrentUser.email
        )
    );
    Notify("Rejected: " & galApproverQueue.Selected.'Request Number', NotificationType.Warning);
    Refresh('Purchase Requests')
)
```

### Approval History Timeline — Items (sorted newest first)
```powerfx
Sort(
    Filter(
        'Approval History',
        'Purchase Request'.'Record ID' = galApproverQueue.Selected.'Record ID'
    ),
    'Decision Date',
    SortOrder.Descending
)
```
