# Quickbase Formula Fields

All formulas apply to the **Deals** table unless otherwise noted.

---

## Contacts Table Formulas

### Field: Contact ID (Text)
```
"CNT-" & ToText([Record ID#])
```

### Field: Full Name (Text)
```
[First Name] & " " & [Last Name]
```

### Field: Lead Score Grade (Text)
Translates the numeric lead score (set by Python scorer) into an A–D letter grade.

```
If(
  [Lead Score] >= 75, "A – Hot",
  If(
    [Lead Score] >= 50, "B – Warm",
    If(
      [Lead Score] >= 25, "C – Cool",
      "D – Cold"
    )
  )
)
```

### Field: Days Since Last Activity — Contacts (Numeric)
```
If(
  IsNull([Last Activity Date]),
  DateDiff(Now(), [Date Created], "days"),
  DateDiff(Now(), [Last Activity Date], "days")
)
```

---

## Deals Table Formulas

### Field: Deal ID (Text)
```
"DL-" & ToText([Record ID#])
```

---

### Field: Win Probability % (Numeric)
Driven by stage. Matches the seed data in the Pipeline Stages table.

```
Case(
  [Stage],
  "New Lead",      5,
  "Qualified",     20,
  "Proposal Sent", 40,
  "Negotiation",   70,
  "Verbal Commit", 85,
  "Closed Won",    100,
  "Closed Lost",   0,
  "On Hold",       0,
  5
)
```

---

### Field: Weighted Value (Numeric — Currency)
The statistically expected revenue from this deal. Used for pipeline forecasting.

```
[Deal Value] * ToNumber([Win Probability %]) / 100
```

---

### Field: Days in Stage (Numeric)
How long the deal has been in its current stage.

```
If(
  IsNull([Stage Changed Date]),
  DateDiff(Now(), [Date Created], "days"),
  DateDiff(Now(), [Stage Changed Date], "days")
)
```

---

### Field: Days Since Last Activity (Numeric)
```
If(
  IsNull([Last Activity Date]),
  DateDiff(Now(), [Date Created], "days"),
  DateDiff(Now(), [Last Activity Date], "days")
)
```

---

### Field: Deal Age Days (Numeric)
Total lifetime of the deal from creation.

```
DateDiff(
  If(IsNull([Actual Close Date]), Now(), [Actual Close Date]),
  [Date Created],
  "days"
)
```

---

### Field: Days to Close Expected (Numeric)
Positive = days remaining. Negative = already past expected close date.

```
If(
  [Stage] = "Closed Won" or [Stage] = "Closed Lost",
  null(),
  DateDiff([Expected Close Date], Today(), "days")
)
```

---

### Field: Is Overdue (Checkbox)
True when the deal has passed its expected close date without being closed.

```
If(
  ([Stage] <> "Closed Won") and
  ([Stage] <> "Closed Lost") and
  (Today() > [Expected Close Date]),
  true(),
  false()
)
```

---

### Field: Follow-up Status (Text)
```
If(
  [Stage] = "Closed Won" or [Stage] = "Closed Lost",
  "Closed",
  If(
    IsNull([Next Follow-up Date]),
    "No Follow-up Set",
    If(
      Today() > [Next Follow-up Date],
      "Overdue",
      If(
        Today() = [Next Follow-up Date],
        "Due Today",
        "On Track"
      )
    )
  )
)
```

---

### Field: Forecast Category (Text)
Maps deals into standard sales forecast buckets.

```
If(
  [Stage] = "Closed Won",
  "Closed",
  If(
    [Stage] = "Closed Lost" or [Stage] = "On Hold",
    "Omit",
    If(
      [Win Probability %] >= 85,
      "Commit",
      If(
        [Win Probability %] >= 40,
        "Best Case",
        "Pipeline"
      )
    )
  )
)
```

---

### Field: Deal Health Score (Numeric — 0 to 100)
A composite health indicator. Lower = more at risk.

```
Max(
  0,
  Min(
    100,
    100
    - If([Days Since Last Activity] > 14, 30, If([Days Since Last Activity] > 7, 15, 0))
    - If([Is Overdue], 25, If([Days to Close Expected] < 7, 10, 0))
    - If([Days in Stage] > LookUp('Pipeline Stages', [Stage Name] = [Stage], [Max Days Recommended]), 20, 0)
    - If(IsNull([Next Follow-up Date]), 15, 0)
    - If([Follow-up Status] = "Overdue", 10, 0)
  )
)
```

---

### Field: Deal Health Label (Text)
```
If(
  [Deal Health Score] >= 75, "Healthy",
  If(
    [Deal Health Score] >= 50, "Needs Attention",
    If(
      [Deal Health Score] >= 25, "At Risk",
      "Stalled"
    )
  )
)
```

---

### Field: Deal Health Color (Text)
```
Case(
  [Deal Health Label],
  "Healthy",          "#27AE60",
  "Needs Attention",  "#F39C12",
  "At Risk",          "#E67E22",
  "Stalled",          "#E74C3C",
  "#95A5A6"
)
```

---

### Field: Stage Badge (Rich Text)
Color-coded stage pill for reports and form views.

```
"<span style='background-color:" &
  Case(
    [Stage],
    "New Lead",      "#3498DB",
    "Qualified",     "#9B59B6",
    "Proposal Sent", "#E67E22",
    "Negotiation",   "#F39C12",
    "Verbal Commit", "#27AE60",
    "Closed Won",    "#1ABC9C",
    "Closed Lost",   "#E74C3C",
    "On Hold",       "#95A5A6",
    "#BDC3C7"
  ) &
  ";color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:bold;'>" &
  [Stage] & "</span>"
```

---

### Field: Priority Badge (Rich Text)
```
"<span style='background-color:" &
  Case([Priority], "High", "#E74C3C", "Medium", "#F39C12", "Low", "#27AE60", "#95A5A6") &
  ";color:#fff;padding:2px 8px;border-radius:3px;font-weight:bold;'>" &
  [Priority] & "</span>"
```

---

### Field: Summary Line (Text)
One-line deal summary for notifications and Teams cards.

```
[Deal ID] & " | " & [Deal Name] & " | " & [Stage] &
" | " & "$" & ToText([Deal Value]) & " | " &
"Close: " & ToText([Expected Close Date])
```

---

### Field: Stalled Alert (Checkbox)
True when there has been no activity for more than 14 days on an active deal.

```
If(
  ([Stage] <> "Closed Won") and
  ([Stage] <> "Closed Lost") and
  ([Days Since Last Activity] > 14),
  true(),
  false()
)
```

---

## Deal Products Table Formulas

### Field: Line Total (Numeric — Currency)
```
ToNumber([Quantity]) *
ToNumber([Unit Price]) *
(1 - ToNumber([Discount %]) / 100)
```

---

## Sales Reps Table Formulas

### Field: Quota Attainment % (Numeric)
```
If(
  ToNumber([Quota (Monthly)]) > 0,
  Round(
    ToNumber([Won This Month]) / ToNumber([Quota (Monthly)]) * 100,
    1
  ),
  0
)
```

### Field: Quota Status (Text)
```
If(
  [Quota Attainment %] >= 100, "Achieved",
  If(
    [Quota Attainment %] >= 75, "On Track",
    If(
      [Quota Attainment %] >= 50, "At Risk",
      "Behind"
    )
  )
)
```

### Field: Quota Status Color (Text)
```
Case(
  [Quota Status],
  "Achieved",  "#1ABC9C",
  "On Track",  "#27AE60",
  "At Risk",   "#F39C12",
  "Behind",    "#E74C3C",
  "#95A5A6"
)
```
