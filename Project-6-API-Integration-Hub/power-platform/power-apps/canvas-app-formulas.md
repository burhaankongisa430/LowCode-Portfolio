# Power Apps — Integration Admin Portal (Power Fx)

Admin console for monitoring integration health, managing routes, and reviewing the dead letter queue.
Restricted to the integration ops team via Entra ID group.

---

## App OnStart

```powerfx
Set(gblCurrentUser, { email: User().Email, name: User().FullName });

ClearCollect(colStatusFilters, ["All", "Success", "Failed", "Dead Letter", "Skipped", "Processing"]);
ClearCollect(colSourceFilters, ["All", "BambooHR", "Jira", "Salesforce", "Web Form", "Quickbase"]);

// Load latest event stats
Set(gblTodayStats, {
    total:    CountIf('Integration Events', DateValue('Date Created') = Today()),
    success:  CountIf('Integration Events', Status = "Success" && DateValue('Date Created') = Today()),
    failed:   CountIf('Integration Events', 'Is Failed' && DateValue('Date Created') = Today()),
    dlq:      CountIf('Dead Letter Queue', Status = "Pending"),
    avgMs:    Average(Filter('Integration Events', DateValue('Date Created') = Today()), 'Processing Time ms')
});

Navigate(scrEventLog, ScreenTransition.Fade)
```

---

## Screen: Event Log (scrEventLog)

### KPI Bar — Total Today
```powerfx
gblTodayStats.total
```

### KPI Bar — Success Rate
```powerfx
If(
    gblTodayStats.total > 0,
    Text(gblTodayStats.success / gblTodayStats.total * 100, "0.0") & "%",
    "—"
)
```

### KPI Bar — Success Rate Color
```powerfx
If(
    gblTodayStats.total = 0, RGBA(149, 165, 166, 1),
    gblTodayStats.success / gblTodayStats.total >= 0.95, RGBA(39, 174, 96, 1),
    gblTodayStats.success / gblTodayStats.total >= 0.80, RGBA(243, 156, 18, 1),
    RGBA(231, 76, 60, 1)
)
```

### KPI Bar — Open DLQ
```powerfx
gblTodayStats.dlq
```

### KPI Bar — DLQ Color
```powerfx
If(gblTodayStats.dlq = 0, RGBA(39, 174, 96, 1),
If(gblTodayStats.dlq <= 5, RGBA(243, 156, 18, 1), RGBA(231, 76, 60, 1)))
```

### Event Gallery — Items
```powerfx
Sort(
    Filter(
        'Integration Events',
        (drpStatusFilter.Selected.Value = "All" || Status = drpStatusFilter.Selected.Value) &&
        (drpSourceFilter.Selected.Value = "All" || 'Source System' = drpSourceFilter.Selected.Value) &&
        (IsBlank(txtSearch.Text) ||
         'Event ID' in txtSearch.Text ||
         'Event Type' in txtSearch.Text ||
         'Source Entity ID' in txtSearch.Text)
    ),
    'Date Created',
    SortOrder.Descending
)
```

### Event Row — Left Border Color
```powerfx
ColorValue(ThisItem.'Status Color')
```

### Event Row — Status Icon
```powerfx
ThisItem.'Status Icon'
```

### Processing Time Label
```powerfx
If(
    IsBlank(ThisItem.'Processing Time ms'),
    "—",
    If(
        ThisItem.'Processing Time ms' < 1000,
        Text(ThisItem.'Processing Time ms', "0") & "ms",
        Text(ThisItem.'Processing Time ms' / 1000, "0.00") & "s"
    )
)
```

### Event Detail Panel — OnSelect (show expanded JSON)
```powerfx
Set(gblSelectedEvent, galEvents.Selected);
UpdateContext({ctxShowDetail: true})
```

### Retry Button (for failed events) — OnSelect
```powerfx
If(
    galEvents.Selected.Status <> "Failed",
    Notify("Only failed events can be retried.", NotificationType.Warning),

    Set(
        gblRetryResult,
        HubRetryFlow.Run(galEvents.Selected.'Record ID', galEvents.Selected.Payload)
    );
    If(
        gblRetryResult.success,
        Notify("Event " & galEvents.Selected.'Event ID' & " retried successfully.", NotificationType.Success),
        Notify("Retry failed: " & gblRetryResult.error, NotificationType.Error)
    );
    Refresh('Integration Events')
)
```

---

## Screen: Route Manager (scrRouteManager)

### Route Gallery — Items
```powerfx
SortByColumns(
    Filter(
        'Integration Routes',
        drpRouteFilter.Selected.Value = "All" ||
        'Source System' = drpRouteFilter.Selected.Value
    ),
    "Priority",
    SortOrder.Ascending
)
```

### Route Health Badge — Fill
```powerfx
ColorValue(ThisItem.'Route Health Color')
```

### Event Count Sparkline label
```powerfx
"Today: " & Text(ThisItem.'Event Count Today', "0") &
" ✅ " & Text(ThisItem.'Success Count Today', "0") &
" ❌ " & Text(ThisItem.'Failure Count Today', "0")
```

### Toggle Route Active — OnChange
```powerfx
Patch(
    'Integration Routes',
    galRoutes.Selected,
    {'Is Active': togRouteActive.Value}
);
Notify(
    "Route " & galRoutes.Selected.'Route ID' & " " &
    If(togRouteActive.Value, "activated.", "deactivated."),
    NotificationType.Success
)
```

### New Route Button — OnSelect
```powerfx
NewForm(frmRoute);
Navigate(scrRouteForm, ScreenTransition.Cover)
```

---

## Screen: Dead Letter Queue (scrDLQ)

### DLQ Gallery — Items
```powerfx
SortByColumns(
    Filter(
        'Dead Letter Queue',
        (drpDLQFilter.Selected.Value = "All" || Status = drpDLQFilter.Selected.Value)
    ),
    "First Failed At",
    SortOrder.Ascending
)
```

### Priority Badge — Fill
```powerfx
Switch(
    ThisItem.Priority,
    "Critical — Stale", RGBA(231, 76, 60, 1),
    "High — Review",    RGBA(230, 126, 34, 1),
    "Medium",           RGBA(243, 156, 18, 1),
    RGBA(149, 165, 166, 1)
)
```

### Manual Retry Button — OnSelect
```powerfx
If(
    IsBlank(galDLQ.Selected.'Original Payload'),
    Notify("No payload available to retry.", NotificationType.Warning),

    Patch(
        'Dead Letter Queue',
        galDLQ.Selected,
        {Status: "Retrying", 'Last Retry At': Now()}
    );
    Notify("Retry queued for " & galDLQ.Selected.'DLQ ID', NotificationType.Information)
)
```

### Abandon Button — OnSelect
```powerfx
Patch(
    'Dead Letter Queue',
    galDLQ.Selected,
    {
        Status: "Abandoned",
        'Resolution Notes': txtAbandonReason.Text,
        'Resolved By': gblCurrentUser.name
    }
);
Notify("Event abandoned — recorded in audit log.", NotificationType.Warning);
Refresh('Dead Letter Queue')
```

---

## Screen: Health Dashboard (scrHealthDashboard)

### Health Grid — Items
```powerfx
Sort('Integration Health', 'Success Rate', SortOrder.Ascending)
```

### Health Status Dot — Fill
```powerfx
ColorValue(ThisItem.'Health Color')
```

### Volume Trend Bar — Width
```powerfx
(ThisItem.'Total Events' / Max('Integration Health', 'Total Events')) * (Parent.Width - 16)
```
