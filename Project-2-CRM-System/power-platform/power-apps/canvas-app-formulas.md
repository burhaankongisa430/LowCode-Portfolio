# Power Apps Canvas App — Power Fx Formulas

CRM portal with four screens: Pipeline Board, Deal Detail, Contact Manager, and Manager Dashboard.

---

## App OnStart

```powerfx
// Cache current user and role
Set(
    gblCurrentUser,
    {
        email:     User().Email,
        name:      User().FullName,
        isManager: User().Email in ["manager@company.com", "vp-sales@company.com"],
        repRecord: LookUp('Sales Reps', Email = User().Email)
    }
);

// Load pipeline stage reference data
ClearCollect(
    colPipelineStages,
    Table(
        {Stage: "New Lead",      Order: 1, Color: "#3498DB", WinProb: 5},
        {Stage: "Qualified",     Order: 2, Color: "#9B59B6", WinProb: 20},
        {Stage: "Proposal Sent", Order: 3, Color: "#E67E22", WinProb: 40},
        {Stage: "Negotiation",   Order: 4, Color: "#F39C12", WinProb: 70},
        {Stage: "Verbal Commit", Order: 5, Color: "#27AE60", WinProb: 85},
        {Stage: "Closed Won",    Order: 6, Color: "#1ABC9C", WinProb: 100},
        {Stage: "Closed Lost",   Order: 7, Color: "#E74C3C", WinProb: 0},
        {Stage: "On Hold",       Order: 8, Color: "#95A5A6", WinProb: 0}
    )
);

// Load loss reasons for dropdown
ClearCollect(
    colLossReasons,
    ["Price", "Competitor", "No Budget", "No Decision", "Wrong Fit", "Timing"]
);

Navigate(scrPipelineBoard, ScreenTransition.Fade)
```

---

## Screen: Pipeline Board (scrPipelineBoard)

### Pipeline Column Gallery — Items
Each column is one stage. Nested gallery inside shows deals for that stage.

```powerfx
// Outer gallery: stages
Sort(colPipelineStages, Order, SortOrder.Ascending)
```

### Inner Deal Gallery — Items (inside each stage column)
```powerfx
Sort(
    Filter(
        Deals,
        Stage = ThisItem.Stage &&
        (gblCurrentUser.isManager || 'Sales Rep'.Email = gblCurrentUser.email) &&
        (IsBlank(txtSearch.Text) ||
         'Deal Name' in txtSearch.Text ||
         'Deal ID' in txtSearch.Text)
    ),
    'Weighted Value',
    SortOrder.Descending
)
```

### Deal Card — Fill (SLA/Health color stripe)
```powerfx
Switch(
    ThisItem.'Deal Health Label',
    "Healthy",         RGBA(39, 174, 96, 0.1),
    "Needs Attention", RGBA(243, 156, 18, 0.1),
    "At Risk",         RGBA(230, 126, 34, 0.1),
    "Stalled",         RGBA(231, 76, 60, 0.12),
    White
)
```

### Deal Card — Follow-up Badge Text
```powerfx
Switch(
    ThisItem.'Follow-up Status',
    "Overdue",         "⚠ Overdue",
    "Due Today",       "⏰ Due Today",
    "On Track",        "✅ On Track",
    "No Follow-up Set","📌 Set Follow-up",
    ""
)
```

### Deal Card — Follow-up Badge Fill
```powerfx
Switch(
    ThisItem.'Follow-up Status',
    "Overdue",         RGBA(231, 76, 60, 1),
    "Due Today",       RGBA(243, 156, 18, 1),
    "On Track",        RGBA(39, 174, 96, 1),
    "No Follow-up Set",RGBA(149, 165, 166, 1),
    RGBA(189, 195, 199, 1)
)
```

### Stage Column Header — Deal Count + Total Value
```powerfx
Text(
    CountIf(
        Deals,
        Stage = ThisItem.Stage &&
        (gblCurrentUser.isManager || 'Sales Rep'.Email = gblCurrentUser.email)
    ), "0"
) &
" deals · $" &
Text(
    Sum(
        Filter(
            Deals,
            Stage = ThisItem.Stage &&
            (gblCurrentUser.isManager || 'Sales Rep'.Email = gblCurrentUser.email)
        ),
        'Weighted Value'
    ),
    "[$-en-ZA]#,##0"
)
```

### Quick Add Deal Button — OnSelect
```powerfx
NewForm(frmNewDeal);
Set(gblNewDealStage, ThisItem.Stage);
Navigate(scrDealDetail, ScreenTransition.Cover)
```

---

## Screen: Deal Detail (scrDealDetail)

### Deal Form — OnSuccess (Submit)
```powerfx
If(
    FormMode.New = frmDealDetail.Mode,
    // New deal: call intake flow to score and assign
    Set(
        gblNewDealResult,
        CRMIntakeFlow.Run(
            txtDealName.Text,
            drpStage.Selected.Stage,
            txtDealValue.Text,
            drpContact.Selected.'Record ID',
            drpCompany.Selected.'Record ID',
            gblCurrentUser.email,
            datExpectedClose.SelectedDate,
            drpLeadSource.Selected.Value
        )
    ),
    // Existing deal: patch directly
    Patch(
        Deals,
        galDeals.Selected,
        {
            'Deal Name':         txtDealName.Text,
            Stage:               drpStage.Selected.Stage,
            'Deal Value':        Value(txtDealValue.Text),
            'Expected Close Date': datExpectedClose.SelectedDate,
            'Next Follow-up Date': datFollowUp.SelectedDate,
            Priority:            drpPriority.Selected.Value,
            Tags:                txtTags.Text
        }
    )
);
Notify("Deal saved successfully.", NotificationType.Success);
Navigate(scrPipelineBoard, ScreenTransition.Back)
```

### Log Activity Button — OnSelect
```powerfx
Collect(
    colPendingActivities,
    {
        DealId:        galDeals.Selected.'Record ID',
        ContactId:     galDeals.Selected.'Primary Contact'.'Record ID',
        ActivityType:  drpActivityType.Selected.Value,
        Subject:       txtActivitySubject.Text,
        Notes:         txtActivityNotes.Text,
        ActivityDate:  Now(),
        Outcome:       drpActivityOutcome.Selected.Value,
        LoggedBy:      gblCurrentUser.name,
        FollowUpDate:  datActivityFollowUp.SelectedDate
    }
);

// Write to Quickbase immediately
Patch(
    Activities,
    Defaults(Activities),
    {
        Deal:           {Id: galDeals.Selected.'Record ID'},
        Contact:        {Id: galDeals.Selected.'Primary Contact'.'Record ID'},
        'Activity Type':drpActivityType.Selected.Value,
        Subject:        txtActivitySubject.Text,
        Notes:          txtActivityNotes.Text,
        'Activity Date':Now(),
        Outcome:        drpActivityOutcome.Selected.Value,
        'Logged By':    gblCurrentUser.name,
        'Logged By Email': gblCurrentUser.email,
        Source:         "Manual",
        'Follow-up Date': datActivityFollowUp.SelectedDate,
        'Follow-up Required': !IsBlank(datActivityFollowUp.SelectedDate)
    }
);

// Update deal follow-up date if set
If(
    !IsBlank(datActivityFollowUp.SelectedDate),
    Patch(
        Deals,
        galDeals.Selected,
        {'Next Follow-up Date': datActivityFollowUp.SelectedDate}
    )
);

Reset(drpActivityType);
Reset(txtActivitySubject);
Reset(txtActivityNotes);
Notify("Activity logged.", NotificationType.Success)
```

### Mark Closed Won Button — OnSelect
```powerfx
If(
    IsBlank(galDeals.Selected.'Deal Name'),
    Notify("No deal selected.", NotificationType.Warning),
    
    UpdateContext({ctxConfirmClose: true})
)
// Confirmation dialog handles the actual patch:
// Patch(Deals, galDeals.Selected, {Stage: "Closed Won", 'Actual Close Date': Today()})
```

### Mark Closed Lost — Validate Loss Reason
```powerfx
If(
    IsBlank(drpLossReason.Selected.Value),
    Notify("Please select a Loss Reason before marking the deal lost.", NotificationType.Warning),

    Patch(
        Deals,
        galDeals.Selected,
        {
            Stage:            "Closed Lost",
            'Loss Reason':    drpLossReason.Selected.Value,
            'Loss Notes':     txtLossNotes.Text,
            'Actual Close Date': Today()
        }
    );
    Notify("Deal marked as lost. Loss reason recorded.", NotificationType.Success);
    Navigate(scrPipelineBoard, ScreenTransition.Back)
)
```

### Activities Timeline Gallery — Items
```powerfx
Sort(
    Filter(
        Activities,
        Deal.'Record ID' = galDeals.Selected.'Record ID'
    ),
    'Activity Date',
    SortOrder.Descending
)
```

### Activity Row — Icon based on type
```powerfx
Switch(
    ThisItem.'Activity Type',
    "Email Sent",     Icon.Mail,
    "Email Received", Icon.Mail,
    "Call",           Icon.Phone,
    "Meeting",        Icon.CalendarBlank,
    "Demo",           Icon.Video,
    "Proposal",       Icon.Documents,
    "LinkedIn",       Icon.Person,
    "Stage Change",   Icon.Trending,
    Icon.Message
)
```

---

## Screen: Contact Manager (scrContactManager)

### Contact Gallery — Items
```powerfx
SortByColumns(
    Filter(
        Contacts,
        (IsBlank(txtContactSearch.Text) ||
         'Full Name' in txtContactSearch.Text ||
         Email in txtContactSearch.Text ||
         'Company - Company Name' in txtContactSearch.Text) &&
        (drpContactType.Selected.Value = "All" || 'Contact Type' = drpContactType.Selected.Value)
    ),
    "Last Name", SortOrder.Ascending
)
```

### Lead Score Pill — Fill
```powerfx
Switch(
    ThisItem.'Lead Score Grade',
    "A – Hot",   RGBA(231, 76, 60, 1),
    "B – Warm",  RGBA(230, 126, 34, 1),
    "C – Cool",  RGBA(52, 152, 219, 1),
    "D – Cold",  RGBA(149, 165, 166, 1),
    RGBA(189, 195, 199, 1)
)
```

---

## Screen: Manager Dashboard (scrManagerDashboard)
*Visible only when `gblCurrentUser.isManager = true`*

### KPI: Total Pipeline Value (Weighted)
```powerfx
Text(
    Sum(
        Filter(Deals, Stage <> "Closed Won" && Stage <> "Closed Lost"),
        'Weighted Value'
    ),
    "[$-en-ZA]R #,##0"
)
```

### KPI: Won This Month
```powerfx
Text(
    Sum(
        Filter(
            Deals,
            Stage = "Closed Won" &&
            Month('Actual Close Date') = Month(Today()) &&
            Year('Actual Close Date') = Year(Today())
        ),
        'Deal Value'
    ),
    "[$-en-ZA]R #,##0"
)
```

### KPI: Deals At Risk or Stalled
```powerfx
CountIf(
    Deals,
    'Deal Health Label' in ["At Risk", "Stalled"] &&
    Stage <> "Closed Won" &&
    Stage <> "Closed Lost"
)
```

### KPI: Win Rate (This Quarter)
```powerfx
Text(
    RoundDown(
        CountIf(
            Deals,
            Stage = "Closed Won" &&
            DateDiff(Today(), 'Actual Close Date', TimeUnit.Months) <= 3
        ) /
        CountIf(
            Deals,
            (Stage = "Closed Won" || Stage = "Closed Lost") &&
            DateDiff(Today(), 'Actual Close Date', TimeUnit.Months) <= 3
        ) * 100,
        1
    ) & "%",
    ""
)
```

### Rep Leaderboard Gallery — Items
```powerfx
SortByColumns(
    Filter('Sales Reps', 'Is Active'),
    "Won This Month",
    SortOrder.Descending
)
```

### Rep Quota Bar — Width
```powerfx
Min(
    Parent.Width - 16,
    (ThisItem.'Won This Month' / Max(1, ThisItem.'Quota (Monthly)')) * (Parent.Width - 16)
)
```

### Rep Quota Bar — Fill
```powerfx
Switch(
    ThisItem.'Quota Status',
    "Achieved",  RGBA(26, 188, 156, 1),
    "On Track",  RGBA(39, 174, 96, 1),
    "At Risk",   RGBA(243, 156, 18, 1),
    "Behind",    RGBA(231, 76, 60, 1),
    RGBA(189, 195, 199, 1)
)
```
