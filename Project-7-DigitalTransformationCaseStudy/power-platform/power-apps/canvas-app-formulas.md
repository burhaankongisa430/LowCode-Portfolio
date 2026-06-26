# Power Apps — Transformation Tracker Portal (Power Fx)

Two-role portal: Transformation Lead (full access) and Stakeholders (read-only view of progress and ROI).

---

## App OnStart

```powerfx
Set(gblCurrentUser, {
    email:    User().Email,
    name:     User().FullName,
    isLead:   User().Email = "transformation-lead@yourcompany.com",
    isExec:   User().Email in ["ceo@company.com","coo@company.com","cro@company.com","cfo@company.com","chro@company.com"]
});

// Load summary stats
Set(gblSummary, {
    totalBenefitsYTD:    Sum('ROI Measurements', 'Actual Benefits YTD'),
    totalInvestment:     First('ROI Measurements').'Total Investment',
    roiPct:              First(Sort('ROI Measurements', 'Snapshot Date', SortOrder.Descending)).'ROI %',
    milestonesTotal:     CountRows(Milestones),
    milestonesComplete:  CountIf(Milestones, Status = "Complete"),
    initiativesActive:   CountIf(Initiatives, Status <> "Complete" && Status <> "Canceled"),
    alertCount:          CountIf('ROI Measurements', 'Realization Status' = "Underperforming")
});

Navigate(scrDashboard, ScreenTransition.Fade)
```

---

## Screen: Executive Dashboard (scrDashboard)

### ROI Gauge — Value
```powerfx
gblSummary.roiPct / 400  // scale 0-400% to 0-1 for gauge control
```

### ROI Label
```powerfx
Text(gblSummary.roiPct, "0.0") & "%"
```

### Total Benefits YTD Label
```powerfx
"R " & Text(gblSummary.totalBenefitsYTD, "#,##0")
```

### Payback Period Label
```powerfx
If(
    gblSummary.totalBenefitsYTD > 0,
    Text(
        gblSummary.totalInvestment / (gblSummary.totalBenefitsYTD / 12),
        "0.0"
    ) & " months",
    "—"
)
```

### Overall Progress Bar — Width
```powerfx
(gblSummary.milestonesComplete / Max(1, gblSummary.milestonesTotal)) * (Parent.Width - 32)
```

### Overall Progress Label
```powerfx
Text(gblSummary.milestonesComplete, "0") & "/" &
Text(gblSummary.milestonesTotal, "0") & " milestones complete (" &
Text(gblSummary.milestonesComplete / Max(1, gblSummary.milestonesTotal) * 100, "0") & "%)"
```

### Initiative Gallery — Items
```powerfx
Sort(
    Filter(
        Initiatives,
        drpStatusFilter.Selected.Value = "All" || Status = drpStatusFilter.Selected.Value
    ),
    'Start Month',
    SortOrder.Ascending
)
```

### Initiative Card — Progress Bar Width
```powerfx
(ThisItem.'Completion %' / 100) * (Parent.Width - 16)
```

### Initiative Card — Progress Bar Fill
```powerfx
Switch(
    ThisItem.'Schedule Status',
    "On Time",     RGBA(39, 174, 96, 1),
    "In Progress", RGBA(52, 152, 219, 1),
    "Delayed",     RGBA(231, 76, 60, 1),
    "Overdue",     RGBA(142, 68, 173, 1),
    RGBA(189, 195, 199, 1)
)
```

---

## Screen: Benefit Realization (scrBenefitRealization)

### Domain ROI Cards — Items
```powerfx
Table(
    {Domain: "Service Desk",  InitiativeId: "INIT-01", BenefitAnnual: 655200,  Investment: 520000,  Icon: "⚙"},
    {Domain: "CRM / Sales",   InitiativeId: "INIT-02", BenefitAnnual: 1821800, Investment: 480000,  Icon: "💼"},
    {Domain: "HR Onboarding", InitiativeId: "INIT-03", BenefitAnnual: 955425,  Investment: 420000,  Icon: "👥"},
    {Domain: "Procurement",   InitiativeId: "INIT-04", BenefitAnnual: 713400,  Investment: 360000,  Icon: "💰"},
    {Domain: "Intelligence",  InitiativeId: "INIT-05", BenefitAnnual: 340000,  Investment: 180000,  Icon: "📊"},
    {Domain: "Integration",   InitiativeId: "INIT-06", BenefitAnnual: 400750,  Investment: 120000,  Icon: "🔌"}
)
```

### Domain ROI Label
```powerfx
"ROI: " & Text(
    (ThisItem.BenefitAnnual - ThisItem.Investment) / ThisItem.Investment * 100,
    "0"
) & "%"
```

### Domain ROI Fill
```powerfx
With(
    {roi: (ThisItem.BenefitAnnual - ThisItem.Investment) / ThisItem.Investment * 100},
    If(roi >= 300, RGBA(26, 188, 156, 1),
    If(roi >= 150, RGBA(39, 174, 96, 1),
    If(roi >= 50, RGBA(243, 156, 18, 1),
    RGBA(231, 76, 60, 1))))
)
```

### Benefit vs Projected Chart (manual bar gallery)
```powerfx
// Items: months 1-18 of actual vs projected
Filter('ROI Monthly Snapshots', 'Month Number' <= gblCurrentMonth)
```

### Monthly Actual Bar Width
```powerfx
(ThisItem.'Actual Benefits' / Max('ROI Monthly Snapshots', 'Actual Benefits')) * (Parent.Width - 8)
```

### Monthly Projected Bar Width
```powerfx
(ThisItem.'Projected Benefits' / Max('ROI Monthly Snapshots', 'Projected Benefits')) * (Parent.Width - 8)
```

---

## Screen: Initiative Detail (scrInitiativeDetail)

### Milestone Timeline Gallery — Items
```powerfx
Sort(
    Filter(Milestones, Initiative.'Record ID' = galInitiatives.Selected.'Record ID'),
    'Planned Date',
    SortOrder.Ascending
)
```

### Milestone Row — Left Dot Color
```powerfx
Switch(
    ThisItem.Status,
    "Complete",   RGBA(39, 174, 96, 1),
    "In Progress",RGBA(52, 152, 219, 1),
    "Overdue",    RGBA(231, 76, 60, 1),
    RGBA(189, 195, 199, 1)
)
```

### Process Improvement Gallery — Items (before/after metrics)
```powerfx
Filter('Process Baselines', Initiative.'Record ID' = galInitiatives.Selected.'Record ID')
```

### Improvement Arrow Text
```powerfx
If(
    ThisItem.'Target Met',
    "✅ " & Text(Abs(ThisItem.'Improvement %'), "0.0") & "% improvement",
    "⚠ " & Text(Abs(ThisItem.'Improvement %'), "0.0") & "% (target: " & Text(Abs(ThisItem.'Target Improvement %'), "0.0") & "%)"
)
```

### Log Actual Metric Button — OnSelect (Lead only)
```powerfx
If(
    Not(gblCurrentUser.isLead),
    Notify("Only the Transformation Lead can update metrics.", NotificationType.Warning),

    Patch(
        'Process Baselines',
        galMetrics.Selected,
        {
            'After Value': Value(txtActualValue.Text),
            'Measurement Date': Today(),
            'Measured By': gblCurrentUser.name
        }
    );
    Notify("Metric updated.", NotificationType.Success);
    Refresh('Process Baselines')
)
```

---

## Screen: Lessons Learned (scrLessonsLearned)

### Lessons Gallery — Items
```powerfx
SortByColumns(
    Filter(
        'Lessons Learned',
        drpCategoryFilter.Selected.Value = "All" ||
        Category = drpCategoryFilter.Selected.Value
    ),
    "Date Captured",
    SortOrder.Descending
)
```

### Impact Badge Fill
```powerfx
Switch(
    ThisItem.Impact,
    "High",   RGBA(231, 76, 60, 1),
    "Medium", RGBA(243, 156, 18, 1),
    "Low",    RGBA(39, 174, 96, 1),
    RGBA(189, 195, 199, 1)
)
```

### Add Lesson Button — OnSelect
```powerfx
Patch(
    'Lessons Learned',
    Defaults('Lessons Learned'),
    {
        Title:         txtLessonTitle.Text,
        Description:   txtLessonBody.Text,
        Category:      drpLessonCategory.Selected.Value,
        Impact:        drpLessonImpact.Selected.Value,
        Initiative:    {Id: galInitiatives.Selected.'Record ID'},
        'Captured By': gblCurrentUser.name,
        'Date Captured': Today()
    }
);
Notify("Lesson saved.", NotificationType.Success);
Reset(txtLessonTitle); Reset(txtLessonBody)
```
