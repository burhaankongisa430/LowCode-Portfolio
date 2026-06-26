# Quickbase Formula Fields — API Integration Hub

---

## Integration Events Table

### Field: Event ID (Text)
```
"EVT-" & Right("000000" & ToText([Record ID#]), 6)
```

### Field: Processing Time Label (Text)
Human-readable processing time for event detail views.
```
If(
  IsNull([Processing Time ms]), "—",
  If(
    [Processing Time ms] < 1000,
    ToText([Processing Time ms]) & "ms",
    ToText(Round(ToNumber([Processing Time ms]) / 1000, 2)) & "s"
  )
)
```

### Field: Status Icon (Text)
Used in reports and detail views for quick visual scanning.
```
Case(
  [Status],
  "Success",     "✅",
  "Failed",      "❌",
  "Dead Letter", "☠",
  "Processing",  "⏳",
  "Received",    "📥",
  "Skipped",     "⏭",
  "—"
)
```

### Field: Status Color (Text)
```
Case(
  [Status],
  "Success",     "#27AE60",
  "Failed",      "#E74C3C",
  "Dead Letter", "#8E44AD",
  "Processing",  "#3498DB",
  "Received",    "#95A5A6",
  "Skipped",     "#BDC3C7",
  "#95A5A6"
)
```

### Field: Is Failed (Checkbox)
```
[Status] = "Failed" or [Status] = "Dead Letter"
```

### Field: Route Label (Text)
Combines source → target for readable event summaries.
```
[Source System] & " → " & [Target System] & " (" & [Event Type] & ")"
```

### Field: Age Minutes (Numeric)
How long ago this event was processed.
```
DateDiff(Now(), [Date Created], "minutes")
```

---

## Integration Routes Table

### Field: Route ID (Text)
```
"R" & Right("00" & ToText([Record ID#]), 2)
```

### Field: Failure Rate Today (Numeric %)
```
If(
  ToNumber([Event Count Today]) > 0,
  Round(ToNumber([Failure Count Today]) / ToNumber([Event Count Today]) * 100, 1),
  0
)
```

### Field: Route Health (Text)
```
If(
  Not([Is Active]), "Inactive",
  If(
    [Failure Rate Today] >= 50, "Down",
    If(
      [Failure Rate Today] >= 20, "Degraded",
      "Healthy"
    )
  )
)
```

### Field: Route Health Color (Text)
```
Case(
  [Route Health],
  "Healthy",  "#27AE60",
  "Degraded", "#F39C12",
  "Down",     "#E74C3C",
  "Inactive", "#95A5A6",
  "#BDC3C7"
)
```

---

## Integration Health Table

### Field: Success Rate (Numeric)
```
If(
  ToNumber([Total Events]) > 0,
  Round(ToNumber([Success Count]) / ToNumber([Total Events]) * 100, 1),
  100
)
```

### Field: Health Status (Text)
```
If(
  [Success Rate] >= 95, "Healthy",
  If(
    [Success Rate] >= 80, "Degraded",
    "Down"
  )
)
```

### Field: Health Color (Text)
```
Case(
  [Health Status],
  "Healthy",  "#27AE60",
  "Degraded", "#F39C12",
  "Down",     "#E74C3C",
  "#95A5A6"
)
```

---

## Dead Letter Queue Table

### Field: DLQ ID (Text)
```
"DLQ-" & ToText([Record ID#])
```

### Field: Days in Queue (Numeric)
```
DateDiff(Now(), [First Failed At], "days")
```

### Field: Priority (Text)
Urgency label based on how long an event has been stuck.
```
If(
  [Days in Queue] >= 7,  "Critical — Stale",
  If(
    [Days in Queue] >= 3, "High — Review",
    If(
      [Days in Queue] >= 1, "Medium",
      "New"
    )
  )
)
```
