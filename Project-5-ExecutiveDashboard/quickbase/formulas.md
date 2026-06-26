# Quickbase Formula Fields — KPI Snapshots Table

---

## Field: Snapshot ID (Text)
```
"SNAP-" & Right("000000" & ToText([Record ID#]), 6)
```

## Field: Snapshot Date (Date)
Extracts the calendar date from the full timestamp for daily grouping in reports.
```
ToDate([Snapshot Time])
```

## Field: Week Number (Numeric)
```
WeekOfYear([Snapshot Time])
```

## Field: Health Status (Text)
Maps the numeric health score to a human-readable label.
```
If(
  [Health Score] >= 85, "Excellent",
  If(
    [Health Score] >= 70, "Good",
    If(
      [Health Score] >= 55, "Needs Attention",
      If(
        [Health Score] >= 40, "At Risk",
        "Critical"
      )
    )
  )
)
```

## Field: Health Color (Text)
```
Case(
  [Health Status],
  "Excellent",       "#27AE60",
  "Good",            "#2ECC71",
  "Needs Attention", "#F39C12",
  "At Risk",         "#E67E22",
  "Critical",        "#E74C3C",
  "#95A5A6"
)
```

## Field: Health Score WoW Change (Numeric)
Requires a summary or a prior snapshot lookup. Approximated as a formula using the previous day's snapshot.
```
[Health Score] - LookUp(
  'KPI Snapshots',
  [Snapshot Date] = DateAdd([Snapshot Date], -7, "days"),
  [Health Score]
)
```

## Field: Weakest Domain (Text)
Identifies which domain is pulling the health score down.
```
If(
  Min([Operational Score], [Commercial Score], [People Score], [Finance Score]) = [Operational Score],
  "Operational",
  If(
    Min([Operational Score], [Commercial Score], [People Score], [Finance Score]) = [Commercial Score],
    "Commercial",
    If(
      Min([Operational Score], [Commercial Score], [People Score], [Finance Score]) = [People Score],
      "People",
      "Finance"
    )
  )
)
```

## Field: Alert Flag (Checkbox)
True when the health score is below the "Needs Attention" threshold.
```
[Health Score] < 70
```

## Field: ETL Coverage (Text)
Shows how many source systems responded (useful for diagnosing ETL failures).
```
ToText([Domains Available]) & " of 4 domains available"
```

## Field: Is Latest Snapshot (Checkbox)
True when this is the most recent snapshot row — used in Power BI to show current state.
```
[Snapshot Time] = Maximum(
  'KPI Snapshots',
  [Snapshot Time]
)
```

## Field: Snapshot Summary (Text)
One-line summary for the weekly email subject line.
```
"Health: " & ToText([Health Score]) & "/100 (" & [Health Status] & ")" &
" | Ops: " & ToText([Operational Score]) &
" | Sales: " & ToText([Commercial Score]) &
" | People: " & ToText([People Score]) &
" | Finance: " & ToText([Finance Score])
```
