# Power Apps — Mobile Executive KPI Viewer (Power Fx)

A phone-layout canvas app for executives. Shows the current health score,
domain scores, KPI cards per domain, and a 7-day trend table.
Connects directly to the QB KPI Snapshots table.

---

## App OnStart

```powerfx
// Load latest KPI snapshot
Set(
    gblLatestSnapshot,
    First(
        Sort(
            'KPI Snapshots',
            'Snapshot Time',
            SortOrder.Descending
        )
    )
);

// Load 7-day trend data
ClearCollect(
    colTrendData,
    Sort(
        Filter(
            'KPI Snapshots',
            'Snapshot Date' >= DateAdd(Today(), -7, TimeUnit.Days)
        ),
        'Snapshot Time',
        SortOrder.Ascending
    )
);

// Load active alerts
ClearCollect(
    colActiveAlerts,
    Filter(
        'KPI Alerts',
        'Alert Time' >= DateAdd(Now(), -24, TimeUnit.Hours) &&
        !Acknowledged
    )
);

Set(gblRefreshTime, Now())
```

---

## Screen: Executive Summary (scrSummary)

### Health Score Label — Text
```powerfx
Text(gblLatestSnapshot.'Health Score', "0") & "/100"
```

### Health Score Ring — Fill color
```powerfx
ColorValue(gblLatestSnapshot.'Health Color')
```

### Health Score Label — Color
```powerfx
ColorValue(gblLatestSnapshot.'Health Color')
```

### Health Status Label — Text
```powerfx
gblLatestSnapshot.'Health Status'
```

### Domain Score Card Gallery — Items
```powerfx
Table(
    {Domain: "Operational",  Score: gblLatestSnapshot.'Operational Score', Icon: "⚙", Weight: "25%"},
    {Domain: "Commercial",   Score: gblLatestSnapshot.'Commercial Score',  Icon: "💼", Weight: "30%"},
    {Domain: "People",       Score: gblLatestSnapshot.'People Score',      Icon: "👥", Weight: "20%"},
    {Domain: "Finance",      Score: gblLatestSnapshot.'Finance Score',     Icon: "💰", Weight: "25%"}
)
```

### Domain Score Card — Fill color
```powerfx
If(
    ThisItem.Score >= 85, RGBA(39, 174, 96, 1),
    If(
        ThisItem.Score >= 70, RGBA(46, 204, 113, 1),
        If(
            ThisItem.Score >= 55, RGBA(243, 156, 18, 1),
            If(
                ThisItem.Score >= 40, RGBA(230, 126, 34, 1),
                RGBA(231, 76, 60, 1)
            )
        )
    )
)
```

### Alert Banner — Visible
```powerfx
CountRows(colActiveAlerts) > 0
```

### Alert Banner — Text
```powerfx
CountRows(colActiveAlerts) & " active KPI alert(s) — tap to view"
```

### Alert Banner — Fill
```powerfx
If(
    CountIf(colActiveAlerts, Severity = "Critical") > 0,
    RGBA(231, 76, 60, 1),
    RGBA(243, 156, 18, 1)
)
```

### Last Refresh Label — Text
```powerfx
"Last updated: " &
Text(gblLatestSnapshot.'Snapshot Time', "ddd d MMM 'at' HH:mm")
```

### Refresh Button — OnSelect
```powerfx
Set(
    gblLatestSnapshot,
    First(Sort('KPI Snapshots', 'Snapshot Time', SortOrder.Descending))
);
Set(gblRefreshTime, Now());
Notify("Dashboard refreshed.", NotificationType.Success)
```

---

## Screen: Domain Detail (scrDomainDetail)

### Domain KPI Gallery — Items
Displays the relevant KPIs for the selected domain.

```powerfx
Switch(
    gblSelectedDomain,
    "Operational",
    Table(
        {KPI: "SLA Met Rate",         Value: Text(gblLatestSnapshot.'SLA Met Rate', "0.0") & "%",    Target: "≥ 90%",  Good: gblLatestSnapshot.'SLA Met Rate' >= 90},
        {KPI: "Active Breaches",      Value: Text(gblLatestSnapshot.'Active Breaches', "0"),          Target: "= 0",    Good: gblLatestSnapshot.'Active Breaches' = 0},
        {KPI: "Avg Resolution (hrs)", Value: Text(gblLatestSnapshot.'Avg Resolution Hours', "0.0"),   Target: "≤ 24h",  Good: gblLatestSnapshot.'Avg Resolution Hours' <= 24},
        {KPI: "Open Tickets",         Value: Text(gblLatestSnapshot.'Open Tickets', "0"),             Target: "Monitor",Good: true}
    ),
    "Commercial",
    Table(
        {KPI: "Weighted Pipeline",    Value: "R" & Text(gblLatestSnapshot.'Weighted Pipeline', "#,##0"), Target: "≥ 3× quota",Good: true},
        {KPI: "Won Revenue MTD",      Value: "R" & Text(gblLatestSnapshot.'Won Revenue MTD', "#,##0"),  Target: "≥ quota",   Good: true},
        {KPI: "Win Rate",             Value: Text(gblLatestSnapshot.'Win Rate', "0.0") & "%",           Target: "≥ 35%",     Good: gblLatestSnapshot.'Win Rate' >= 35},
        {KPI: "Quota Attainment",     Value: Text(gblLatestSnapshot.'Quota Attainment', "0.0") & "%",  Target: "≥ 100%",    Good: gblLatestSnapshot.'Quota Attainment' >= 100},
        {KPI: "Stalled Deals",        Value: Text(gblLatestSnapshot.'Stalled Deals', "0"),             Target: "= 0",       Good: gblLatestSnapshot.'Stalled Deals' = 0}
    ),
    "People",
    Table(
        {KPI: "Active Onboarding",    Value: Text(gblLatestSnapshot.'Active Onboarding', "0"),                      Target: "Monitor",Good: true},
        {KPI: "On Track Rate",        Value: Text(gblLatestSnapshot.'Onboarding On Track Rate', "0.0") & "%",       Target: "≥ 90%",  Good: gblLatestSnapshot.'Onboarding On Track Rate' >= 90},
        {KPI: "Avg Completion Days",  Value: Text(gblLatestSnapshot.'Avg Completion Days', "0.0") & " days",        Target: "≤ 30d",  Good: gblLatestSnapshot.'Avg Completion Days' <= 30},
        {KPI: "Day 1 Readiness",      Value: Text(gblLatestSnapshot.'Day1 Readiness Rate', "0.0") & "%",            Target: "≥ 95%",  Good: gblLatestSnapshot.'Day1 Readiness Rate' >= 95}
    ),
    "Finance",
    Table(
        {KPI: "Committed Spend MTD",  Value: "R" & Text(gblLatestSnapshot.'Committed Spend MTD', "#,##0"),    Target: "≤ budget",   Good: gblLatestSnapshot.'Avg Budget Util' <= 100},
        {KPI: "Avg Budget Util",      Value: Text(gblLatestSnapshot.'Avg Budget Util', "0.0") & "%",           Target: "≤ 85%",      Good: gblLatestSnapshot.'Avg Budget Util' <= 85},
        {KPI: "Pending Approvals",    Value: Text(gblLatestSnapshot.'Pending Approvals', "0"),                  Target: "≤ 10",       Good: gblLatestSnapshot.'Pending Approvals' <= 10},
        {KPI: "Approval Cycle Days",  Value: Text(gblLatestSnapshot.'Approval Cycle Days', "0.0") & " days",   Target: "≤ 2 days",   Good: gblLatestSnapshot.'Approval Cycle Days' <= 2}
    ),
    Table({KPI: "Select a domain", Value: "", Target: "", Good: true})
)
```

### KPI Row — Left Border Color
```powerfx
If(ThisItem.Good, RGBA(39, 174, 96, 1), RGBA(231, 76, 60, 1))
```

### KPI Row — Status Icon
```powerfx
If(ThisItem.Good, "✅", "⚠")
```

---

## Screen: 7-Day Trend (scrTrend)

### Trend Table Gallery — Items
```powerfx
Sort(colTrendData, 'Snapshot Date', SortOrder.Descending)
```

### Trend Row — Score Indicator (mini bar width)
```powerfx
(ThisItem.'Health Score' / 100) * (Parent.Width - 80)
```

### WoW Change Label — Text
```powerfx
With(
    {
        latest: First(Sort(colTrendData, 'Snapshot Date', SortOrder.Descending)).'Health Score',
        weekAgo: First(Sort(
            Filter(colTrendData, 'Snapshot Date' <= DateAdd(Today(), -7, TimeUnit.Days)),
            'Snapshot Date', SortOrder.Descending
        )).'Health Score'
    },
    If(
        IsBlank(weekAgo), "No prior data",
        If(latest > weekAgo, "▲ +" & Text(latest - weekAgo, "0.0") & " pts",
        If(latest < weekAgo, "▼ " & Text(latest - weekAgo, "0.0") & " pts",
        "→ No change"))
    )
)
```

### WoW Change Color
```powerfx
With(
    {
        latest: First(Sort(colTrendData, 'Snapshot Date', SortOrder.Descending)).'Health Score',
        weekAgo: First(Sort(Filter(colTrendData, 'Snapshot Date' <= DateAdd(Today(), -7, TimeUnit.Days)), 'Snapshot Date', SortOrder.Descending)).'Health Score'
    },
    If(latest > weekAgo, RGBA(39, 174, 96, 1),
    If(latest < weekAgo, RGBA(231, 76, 60, 1),
    RGBA(127, 140, 141, 1)))
)
```

---

## Screen: Active Alerts (scrAlerts)

### Alert Gallery — Items
```powerfx
Sort(colActiveAlerts, 'Alert Time', SortOrder.Descending)
```

### Alert Row Fill
```powerfx
If(
    ThisItem.Severity = "Critical",
    RGBA(231, 76, 60, 0.12),
    RGBA(243, 156, 18, 0.1)
)
```

### Alert Severity Icon
```powerfx
If(ThisItem.Severity = "Critical", "🚨", "⚠")
```
