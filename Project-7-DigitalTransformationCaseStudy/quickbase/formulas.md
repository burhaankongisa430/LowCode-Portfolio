# Quickbase Formula Fields — Digital Transformation Tracker

---

## Initiatives Table

### Field: Initiative ID (Text)
```
"INIT-" & Right("00" & ToText([Record ID#]), 2)
```

### Field: Phase (Text)
Maps month number to phase label.
```
If(
  [Start Month] <= 9, "Phase 1 — Operational Foundation",
  "Phase 2 — Enterprise Integration"
)
```

### Field: Schedule Status (Text)
```
If(
  [Actual End Date] > [Planned End Date], "Delayed",
  If(
    IsNull([Actual End Date]) and Today() > [Planned End Date], "Overdue",
    If(
      IsNull([Actual End Date]), "In Progress",
      "On Time"
    )
  )
)
```

### Field: Schedule Variance Days (Numeric)
```
If(
  Not(IsNull([Actual End Date])),
  DateDiff([Actual End Date], [Planned End Date], "days"),
  If(
    IsNull([Actual End Date]) and Today() > [Planned End Date],
    DateDiff(Today(), [Planned End Date], "days"),
    null()
  )
)
```

### Field: Completion % (Numeric)
Driven by summary of milestone completion.
```
If(
  ToNumber([Total Milestones]) > 0,
  Round(ToNumber([Completed Milestones]) / ToNumber([Total Milestones]) * 100, 0),
  0
)
```

### Field: Status Badge (Rich Text)
```
"<span style='background:" &
  Case(
    [Schedule Status],
    "On Time",     "#27AE60",
    "In Progress", "#3498DB",
    "Delayed",     "#E74C3C",
    "Overdue",     "#8E44AD",
    "#95A5A6"
  ) &
  ";color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:bold'>" &
  [Schedule Status] & "</span>"
```

---

## ROI Measurements Table

### Field: ROI % (Numeric)
```
If(
  ToNumber([Total Investment]) > 0,
  Round(
    (ToNumber([Annual Net Benefit]) - ToNumber([Annual OPEX])) /
    ToNumber([Total Investment]) * 100,
    1
  ),
  0
)
```

### Field: Payback Months (Numeric)
```
If(
  (ToNumber([Annual Net Benefit]) - ToNumber([Annual OPEX])) > 0,
  Round(
    ToNumber([Total Investment]) /
    ((ToNumber([Annual Net Benefit]) - ToNumber([Annual OPEX])) / 12),
    1
  ),
  null()
)
```

### Field: Benefit Realization % (Numeric)
Actual benefits achieved vs. projected benefits at this point in time.
```
If(
  ToNumber([Projected Benefits YTD]) > 0,
  Round(
    ToNumber([Actual Benefits YTD]) / ToNumber([Projected Benefits YTD]) * 100,
    1
  ),
  0
)
```

### Field: Realization Status (Text)
```
If(
  [Benefit Realization %] >= 100, "Exceeding",
  If(
    [Benefit Realization %] >= 85, "On Track",
    If(
      [Benefit Realization %] >= 70, "At Risk",
      "Underperforming"
    )
  )
)
```

### Field: Realization Color (Text)
```
Case(
  [Realization Status],
  "Exceeding",       "#1ABC9C",
  "On Track",        "#27AE60",
  "At Risk",         "#F39C12",
  "Underperforming", "#E74C3C",
  "#95A5A6"
)
```

---

## Process Baselines Table

### Field: Improvement % (Numeric)
```
If(
  [Direction] = "Higher is Better",
  Round((ToNumber([After Value]) - ToNumber([Before Value])) / Abs(ToNumber([Before Value])) * 100, 1),
  Round((ToNumber([Before Value]) - ToNumber([After Value])) / Abs(ToNumber([Before Value])) * 100, 1)
)
```

### Field: Target Met (Checkbox)
```
If(
  [Direction] = "Higher is Better",
  ToNumber([After Value]) >= ToNumber([Target Value]),
  ToNumber([After Value]) <= ToNumber([Target Value])
)
```

### Field: KPI Traffic Light (Text)
```
If(
  [Target Met], "🟢",
  If(
    Abs([Improvement %]) >= Abs(ToNumber([Minimum Acceptable Improvement %])), "🟡",
    "🔴"
  )
)
```

---

## Milestones Table

### Field: Milestone ID (Text)
```
"MS-" & Right("000" & ToText([Record ID#]), 3)
```

### Field: Days Variance (Numeric)
```
If(
  Not(IsNull([Actual Date])),
  DateDiff([Actual Date], [Planned Date], "days"),
  If(
    Today() > [Planned Date] and IsNull([Actual Date]),
    DateDiff(Today(), [Planned Date], "days"),
    null()
  )
)
```

### Field: Milestone Status (Text)
```
If(
  [Status] = "Complete", "✅ Complete",
  If(
    IsNull([Actual Date]) and Today() > [Planned Date], "⚠ Overdue",
    If(
      DateDiff([Planned Date], Today(), "days") <= 7, "🔜 Due Soon",
      "📅 Upcoming"
    )
  )
)
```
