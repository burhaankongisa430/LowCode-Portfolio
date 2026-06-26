# Power Apps Canvas App — Power Fx Formulas

Self-service ticket submission portal. Users submit tickets; agents view and update their assigned queue.

---

## App OnStart

```powerfx
// Cache current user and load reference data
Set(
    gblCurrentUser,
    {
        email:       User().Email,
        name:        User().FullName,
        isAgent:     !IsBlank(LookUp('Agents', Email = User().Email)),
        isManager:   User().Email in ["manager1@company.com", "manager2@company.com"]
    }
);

// Load SLA policies for client-side SLA preview
ClearCollect(
    colSLAPolicies,
    Table(
        {Priority: "P1-Critical", ResponseHours: 1,  ResolutionHours: 4},
        {Priority: "P2-High",     ResponseHours: 4,  ResolutionHours: 8},
        {Priority: "P3-Medium",   ResponseHours: 8,  ResolutionHours: 24},
        {Priority: "P4-Low",      ResponseHours: 24, ResolutionHours: 72}
    )
);

// Load categories
ClearCollect(
    colCategories,
    Table(
        {Category: "IT-Hardware",      Team: "IT Support"},
        {Category: "IT-Software",      Team: "IT Support"},
        {Category: "IT-Network",       Team: "IT Support"},
        {Category: "HR-Leave",         Team: "HR"},
        {Category: "HR-Payroll",       Team: "HR"},
        {Category: "HR-Benefits",      Team: "HR"},
        {Category: "Finance-Invoice",  Team: "Finance"},
        {Category: "Finance-Expense",  Team: "Finance"},
        {Category: "Facilities",       Team: "Facilities"}
    )
);

Navigate(If(gblCurrentUser.isAgent, scrAgentQueue, scrSubmitTicket), ScreenTransition.Fade)
```

---

## Screen: Submit Ticket (scrSubmitTicket)

### SLA Preview Label — Text property
Shows the expected resolution deadline based on selected priority before submission.

```powerfx
If(
    IsBlank(drpPriority.Selected.Value),
    "Select a priority to see your SLA commitment",
    "Expected resolution: " &
    Text(
        DateAdd(
            Now(),
            LookUp(colSLAPolicies, Priority = drpPriority.Selected.Value, ResolutionHours),
            TimeUnit.Hours
        ),
        "ddd d MMM yyyy 'at' HH:mm"
    )
)
```

### Category Dropdown — Items property

```powerfx
Sort(colCategories, Category, SortOrder.Ascending)
```

### Priority Dropdown — Items property

```powerfx
Table(
    {Value: "P1-Critical", Label: "🔴 P1 - Critical (4hr SLA)"},
    {Value: "P2-High",     Label: "🟠 P2 - High (8hr SLA)"},
    {Value: "P3-Medium",   Label: "🟡 P3 - Medium (24hr SLA)"},
    {Value: "P4-Low",      Label: "🟢 P4 - Low (72hr SLA)"}
)
```

### Submit Button — OnSelect

```powerfx
If(
    IsBlank(txtTitle.Text) || IsBlank(txtDescription.Text) ||
    IsBlank(drpCategory.Selected.Category) || IsBlank(drpPriority.Selected.Value),

    Notify("Please complete all required fields.", NotificationType.Warning),

    // Proceed with submission
    Set(gblSubmitting, true);

    // Call Power Automate intake flow
    Set(
        gblSubmitResult,
        ServiceDeskIntakeFlow.Run(
            txtTitle.Text,
            txtDescription.Text,
            drpCategory.Selected.Category,
            drpPriority.Selected.Value,
            gblCurrentUser.name,
            gblCurrentUser.email,
            txtTags.Text
        )
    );

    If(
        !IsBlank(gblSubmitResult.ticketId),
        // Success
        Set(
            gblConfirmation,
            {
                ticketId: gblSubmitResult.ticketId,
                dueDate:  gblSubmitResult.dueDate
            }
        );
        Navigate(scrConfirmation, ScreenTransition.Cover),

        // Error
        Notify(
            "Submission failed. Please try again or contact the service desk directly.",
            NotificationType.Error
        )
    );

    Set(gblSubmitting, false)
)
```

### Submit Button — DisplayMode property

```powerfx
If(gblSubmitting, DisplayMode.Disabled, DisplayMode.Edit)
```

### Submit Button — Text property

```powerfx
If(gblSubmitting, "Submitting...", "Submit Ticket")
```

---

## Screen: Confirmation (scrConfirmation)

### Confirmation Label — Text property

```powerfx
"✅ Ticket " & gblConfirmation.ticketId & " has been submitted." &
Char(10) &
"A confirmation has been sent to " & gblCurrentUser.email & "." &
Char(10) &
"Expected resolution: " & Text(DateTimeValue(gblConfirmation.dueDate), "ddd d MMM yyyy 'at' HH:mm")
```

### Track Another Ticket Button — OnSelect

```powerfx
Set(gblConfirmation, Blank());
Navigate(scrSubmitTicket, ScreenTransition.Back)
```

---

## Screen: Agent Queue (scrAgentQueue)

### Gallery — Items property
Shows only tickets assigned to the logged-in agent, sorted by SLA urgency.

```powerfx
Sort(
    Filter(
        Tickets,
        'Assigned Agent'.Email = gblCurrentUser.email &&
        Status <> "Closed" &&
        Status <> "Resolved"
    ),
    'Time Remaining Hours',
    SortOrder.Ascending
)
```

### Gallery Row — Fill property (color-coded by SLA)

```powerfx
Switch(
    ThisItem.'SLA Status',
    "Breached", RGBA(231, 76, 60, 0.15),
    "At Risk",  RGBA(243, 156, 18, 0.15),
    "On Track", RGBA(39, 174, 96, 0.08),
    "Met",      RGBA(41, 128, 185, 0.08),
    White
)
```

### Priority Badge — Text property

```powerfx
Switch(
    ThisItem.Priority,
    "P1-Critical", "🔴 P1",
    "P2-High",     "🟠 P2",
    "P3-Medium",   "🟡 P3",
    "P4-Low",      "🟢 P4",
    ThisItem.Priority
)
```

### Time Remaining Label — Text property

```powerfx
If(
    ThisItem.'SLA Status' = "Breached",
    "⚠ " & Text(Abs(ThisItem.'Time Remaining Hours'), "0.0") & "h overdue",
    If(
        ThisItem.'Time Remaining Hours' < 2,
        "⏰ " & Text(ThisItem.'Time Remaining Hours' * 60, "0") & " min remaining",
        "⏱ " & Text(ThisItem.'Time Remaining Hours', "0.0") & "h remaining"
    )
)
```

### Update Status Dropdown — OnChange (in ticket detail screen)

```powerfx
Patch(
    Tickets,
    galAgentQueue.Selected,
    {
        Status: drpStatusUpdate.Selected.Value,
        'Resolution Date': If(
            drpStatusUpdate.Selected.Value = "Resolved",
            Now(),
            Blank()
        )
    }
);

// Log to audit collection for batch write
Collect(
    colAuditLog,
    {
        TicketRecordId: galAgentQueue.Selected.'Record ID',
        Action:         "Status Change",
        OldValue:       galAgentQueue.Selected.Status,
        NewValue:       drpStatusUpdate.Selected.Value,
        PerformedBy:    gblCurrentUser.name,
        Timestamp:      Now()
    }
);

Notify("Ticket status updated to " & drpStatusUpdate.Selected.Value, NotificationType.Success)
```

---

## Screen: Manager Dashboard (scrManagerDashboard)

### KPI Cards — Open Tickets

```powerfx
CountIf(Tickets, Status <> "Closed" && Status <> "Resolved")
```

### KPI Cards — Breached Today

```powerfx
CountIf(
    Tickets,
    'SLA Status' = "Breached" &&
    DateValue('Date Created') = Today()
)
```

### KPI Cards — Avg Resolution Time (hours)

```powerfx
Average(
    Filter(Tickets, Status = "Resolved" || Status = "Closed"),
    'Resolution Time Hours'
)
```

### KPI Cards — SLA Met Rate (%)

```powerfx
Text(
    CountIf(
        Filter(Tickets, Status = "Resolved" || Status = "Closed"),
        'SLA Status' = "Met"
    ) /
    CountIf(Tickets, Status = "Resolved" || Status = "Closed") * 100,
    "0.0"
) & "%"
```

### Agent Workload Gallery — Items

```powerfx
Sort(
    Filter(Agents, 'Is Active'),
    'Active Ticket Count',
    SortOrder.Descending
)
```

### Agent Capacity Bar — Width property

```powerfx
(ThisItem.'Active Ticket Count' / ThisItem.'Max Capacity') *
(Parent.Width - 40)
```

### Agent Capacity Bar — Fill property

```powerfx
If(
    ThisItem.'Capacity Percentage' >= 100, RGBA(231, 76, 60, 1),
    ThisItem.'Capacity Percentage' >= 80,  RGBA(243, 156, 18, 1),
    RGBA(39, 174, 96, 1)
)
```

---

## Global: Search Filter (applied across list screens)

```powerfx
Filter(
    Tickets,
    (IsBlank(txtSearch.Text) ||
     Title in txtSearch.Text ||
     'Ticket ID' in txtSearch.Text ||
     'Submitter Name' in txtSearch.Text) &&
    (drpFilterStatus.Selected.Value = "All" || Status = drpFilterStatus.Selected.Value) &&
    (drpFilterPriority.Selected.Value = "All" || Priority = drpFilterPriority.Selected.Value) &&
    (drpFilterTeam.Selected.Value = "All" || 'Assigned Team' = drpFilterTeam.Selected.Value)
)
```

---

## Global: Error Handling Template

Used on all screens with data operations.

```powerfx
IfError(
    /* data operation here */,
    Notify(
        "An error occurred: " & FirstError.Message,
        NotificationType.Error
    )
)
```
