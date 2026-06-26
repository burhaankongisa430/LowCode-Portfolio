# Power Apps Canvas App — Power Fx Formulas

Three role-based views in one app: New Hire portal, Manager dashboard, HR admin console.
Role is determined by Entra ID group membership checked at `App.OnStart`.

---

## App OnStart

```powerfx
// Resolve role from Entra ID group membership
Set(
    gblCurrentUser,
    {
        email:     User().Email,
        name:      User().FullName,
        isHR:      !IsBlank(LookUp('HR Admins', Email = User().Email)),
        isManager: !IsBlank(LookUp(Employees, 'Hiring Manager Email' = User().Email)),
        isIT:      User().Email in ["it-lead@company.com", "it-onboarding@company.com"],
        hireRecord:LookUp(Employees, 'Work Email' = User().Email)
    }
);

// Load phase reference data
ClearCollect(
    colPhases,
    Table(
        {Phase: "Pre-boarding", Order: 1, Color: "#3498DB", Icon: "📋"},
        {Phase: "Day 1",        Order: 2, Color: "#9B59B6", Icon: "🌟"},
        {Phase: "Week 1",       Order: 3, Color: "#E67E22", Icon: "🚀"},
        {Phase: "Month 1",      Order: 4, Color: "#27AE60", Icon: "🎯"},
        {Phase: "90 Days",      Order: 5, Color: "#1ABC9C", Icon: "🏆"}
    )
);

// Route to correct home screen based on role
Navigate(
    If(
        gblCurrentUser.isHR,       scrHRConsole,
        If(
            gblCurrentUser.isManager,  scrManagerDashboard,
            If(
                Not(IsBlank(gblCurrentUser.hireRecord)), scrNewHirePortal,
                scrNewHirePortal
            )
        )
    ),
    ScreenTransition.Fade
)
```

---

## Screen: New Hire Portal (scrNewHirePortal)

### Welcome Header — Text property
```powerfx
gblCurrentUser.hireRecord.'Welcome Message'
```

### Progress Ring — Value
```powerfx
gblCurrentUser.hireRecord.'Overall Progress %' / 100
```

### Task Gallery — Items (current phase only, owned by new hire)
```powerfx
Sort(
    Filter(
        'Onboarding Tasks',
        Employee.'Record ID' = gblCurrentUser.hireRecord.'Record ID' &&
        'Owner Role' = "New Hire" &&
        Phase = gblCurrentUser.hireRecord.'Current Phase'
    ),
    'Sort Order',
    SortOrder.Ascending
)
```

### Task Row — Fill (status color)
```powerfx
Switch(
    ThisItem.Status,
    "Completed",   RGBA(39, 174, 96, 0.1),
    "Overdue",     RGBA(231, 76, 60, 0.12),
    "In Progress", RGBA(52, 152, 219, 0.1),
    "Blocked",     RGBA(155, 89, 182, 0.1),
    White
)
```

### Mark Complete Button — OnSelect
```powerfx
If(
    ThisItem.Status = "Completed",
    Notify("This task is already completed.", NotificationType.Information),

    // Patch task status and completion date
    Patch(
        'Onboarding Tasks',
        ThisItem,
        {
            Status:           "Completed",
            'Completed Date': Today(),
            'Completed By':   gblCurrentUser.name
        }
    );

    Notify(
        "✅ " & ThisItem.'Task Name' & " marked as complete!",
        NotificationType.Success
    );

    // Refresh task gallery
    Refresh('Onboarding Tasks')
)
```

### Phase Progress Tabs — Items
```powerfx
colPhases
```

### Phase Tab — Fill (active vs inactive)
```powerfx
If(
    ThisItem.Phase = varSelectedPhase,
    ColorValue(ThisItem.Color),
    RGBA(236, 240, 241, 1)
)
```

### Phase Tab — OnSelect
```powerfx
Set(varSelectedPhase, ThisItem.Phase)
```

### Phase Task Count Badge
```powerfx
Text(
    CountIf(
        'Onboarding Tasks',
        Employee.'Record ID' = gblCurrentUser.hireRecord.'Record ID' &&
        Phase = ThisItem.Phase
    ), "0"
) & "/" &
Text(
    CountIf(
        'Onboarding Tasks',
        Employee.'Record ID' = gblCurrentUser.hireRecord.'Record ID' &&
        Phase = ThisItem.Phase &&
        Status = "Completed"
    ), "0"
)
```

---

## Screen: Manager Dashboard (scrManagerDashboard)

### Direct Reports Gallery — Items
```powerfx
Sort(
    Filter(
        Employees,
        'Hiring Manager Email' = gblCurrentUser.email &&
        'Onboarding Status' <> "Completed"
    ),
    'Overdue Tasks',
    SortOrder.Descending
)
```

### Hire Card — Progress Bar Width
```powerfx
(ThisItem.'Overall Progress %' / 100) * (Parent.Width - 32)
```

### Hire Card — Progress Bar Fill
```powerfx
Switch(
    ThisItem.'Onboarding Health',
    "On Track", RGBA(39, 174, 96, 1),
    "At Risk",  RGBA(243, 156, 18, 1),
    "Delayed",  RGBA(231, 76, 60, 1),
    RGBA(189, 195, 199, 1)
)
```

### Manager Task Gallery — Items (tasks assigned to this manager across all hires)
```powerfx
Sort(
    Filter(
        'Onboarding Tasks',
        'Owner Email' = gblCurrentUser.email &&
        Status <> "Completed" &&
        Status <> "N/A"
    ),
    'Days Until Due',
    SortOrder.Ascending
)
```

### Overdue Count KPI
```powerfx
CountIf(
    'Onboarding Tasks',
    'Owner Email' = gblCurrentUser.email &&
    'Is Overdue'
)
```

### Due Today Count KPI
```powerfx
CountIf(
    'Onboarding Tasks',
    'Owner Email' = gblCurrentUser.email &&
    'Due Date' = Today() &&
    Status <> "Completed"
)
```

### Add Note Button — OnSelect (on hire detail screen)
```powerfx
Patch(
    Employees,
    galManagerHires.Selected,
    { Notes: galManagerHires.Selected.Notes & Char(10) & "[" & Text(Now(), "dd/MM/yyyy HH:mm") & " – " & gblCurrentUser.name & "] " & txtManagerNote.Text }
);
Reset(txtManagerNote);
Notify("Note added.", NotificationType.Success)
```

---

## Screen: HR Admin Console (scrHRConsole)

### All Active Hires Gallery — Items
```powerfx
Filter(
    Employees,
    'Onboarding Status' = "Active" || 'Onboarding Status' = "Pre-boarding"
)
```

### Filtered by Health
```powerfx
Filter(
    Employees,
    (drpHealthFilter.Selected.Value = "All" || 'Onboarding Health' = drpHealthFilter.Selected.Value) &&
    ('Onboarding Status' = "Active" || 'Onboarding Status' = "Pre-boarding") &&
    (IsBlank(txtHRSearch.Text) || 'Full Name' in txtHRSearch.Text || 'Employee ID' in txtHRSearch.Text)
)
```

### KPI: Total Active Onboarding
```powerfx
CountIf(Employees, 'Onboarding Status' = "Active" || 'Onboarding Status' = "Pre-boarding")
```

### KPI: On Track
```powerfx
CountIf(
    Employees,
    'Onboarding Health' = "On Track" &&
    ('Onboarding Status' = "Active" || 'Onboarding Status' = "Pre-boarding")
)
```

### KPI: At Risk
```powerfx
CountIf(
    Employees,
    'Onboarding Health' = "At Risk" &&
    ('Onboarding Status' = "Active" || 'Onboarding Status' = "Pre-boarding")
)
```

### KPI: Delayed
```powerfx
CountIf(
    Employees,
    'Onboarding Health' = "Delayed" &&
    ('Onboarding Status' = "Active" || 'Onboarding Status' = "Pre-boarding")
)
```

### Create New Hire Button — OnSelect
```powerfx
NewForm(frmNewEmployee);
Navigate(scrNewHireForm, ScreenTransition.Cover)
```

### New Hire Form — OnSuccess
```powerfx
// After form submit, trigger task generation
Set(
    gblNewHireResult,
    OnboardingTaskGeneratorFlow.Run(
        frmNewEmployee.LastSubmit.'Record ID',
        frmNewEmployee.LastSubmit.'Employee ID',
        frmNewEmployee.LastSubmit.'First Name',
        frmNewEmployee.LastSubmit.'Last Name',
        frmNewEmployee.LastSubmit.'Personal Email',
        frmNewEmployee.LastSubmit.'Job Title',
        frmNewEmployee.LastSubmit.'Department - Department Name',
        Text(frmNewEmployee.LastSubmit.'Start Date', "yyyy-MM-dd"),
        frmNewEmployee.LastSubmit.'Employment Type',
        frmNewEmployee.LastSubmit.'Work Location',
        frmNewEmployee.LastSubmit.'Hiring Manager Email'
    )
);

Notify(
    "✅ " & frmNewEmployee.LastSubmit.'Full Name' & " created — " &
    gblNewHireResult.tasksCreated & " onboarding tasks generated.",
    NotificationType.Success
);
Navigate(scrHRConsole, ScreenTransition.Back)
```

### Equipment Request Form — OnSelect (submit)
```powerfx
Patch(
    'Equipment Requests',
    Defaults('Equipment Requests'),
    {
        Employee:         {Id: galHRHires.Selected.'Record ID'},
        'Equipment Type': drpEquipmentType.Selected.Value,
        Specification:    txtEquipSpec.Text,
        Quantity:         Value(txtQty.Text),
        'Requested By':   gblCurrentUser.name,
        Status:           "Requested",
        'Required By Date': DateAdd(galHRHires.Selected.'Start Date', -2, TimeUnit.Days)
    }
);
Notify("Equipment request submitted.", NotificationType.Success)
```
