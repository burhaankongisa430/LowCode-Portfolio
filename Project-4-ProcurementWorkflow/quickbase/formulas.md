# Quickbase Formula Fields

---

## Purchase Requests Table

### Field: Request Number (Text)
Zero-padded sequential reference number.
```
"PR-" & Right("00000" & ToText([Record ID#]), 5)
```

### Field: Approval Level Required (Numeric)
Determines how many approval levels this request must pass through.
```
If(
  [Total Amount] > 750000, 4,
  If(
    [Total Amount] > 250000, 3,
    If(
      [Total Amount] > 75000, 2,
      1
    )
  )
)
```

### Field: Amount Band (Text)
Human-readable spend tier for reporting and routing labels.
```
If(
  [Total Amount] > 750000,  "Tier 4 – Above R750k (CEO)",
  If(
    [Total Amount] > 250000, "Tier 3 – R250k–R750k (Finance Director)",
    If(
      [Total Amount] > 75000,  "Tier 2 – R75k–R250k (Dept Head)",
      "Tier 1 – Under R75k (Manager)"
    )
  )
)
```

### Field: Vendor Approved (Checkbox)
True when the selected vendor is on the approved list with an "Approved" status.
```
If(
  Not(IsNull([Vendor])) and [Vendor - Status] = "Approved",
  true(),
  false()
)
```

### Field: Days in Current Status (Numeric)
How many days the request has been in its current status. Used to detect SLA breaches.
```
DateDiff(Now(), [Date Modified], "days")
```

### Field: Approval SLA Hours (Numeric)
The SLA in hours for the current approval level based on the threshold bands.
```
Case(
  [Current Approval Level],
  1, 24,
  2, 48,
  3, 48,
  4, 72,
  24
)
```

### Field: SLA Breached (Checkbox)
True when the request is awaiting approval and has exceeded the SLA.
```
If(
  [Status] in List("Level 1 Pending", "Level 2 Pending", "Level 3 Pending", "Level 4 Pending") and
  DateDiff(Now(), [Date Modified], "hours") > [Approval SLA Hours],
  true(),
  false()
)
```

### Field: Status Color (Text)
```
Case(
  [Status],
  "Draft",            "#95A5A6",
  "Submitted",        "#3498DB",
  "Under Review",     "#9B59B6",
  "Level 1 Pending",  "#E67E22",
  "Level 2 Pending",  "#E67E22",
  "Level 3 Pending",  "#D35400",
  "Level 4 Pending",  "#C0392B",
  "Approved",         "#27AE60",
  "PO Issued",        "#1ABC9C",
  "Rejected",         "#E74C3C",
  "Canceled",        "#BDC3C7",
  "#95A5A6"
)
```

### Field: Status Badge (Rich Text)
```
"<span style='background:" & [Status Color] &
";color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold'>" &
[Status] & "</span>"
```

### Field: Urgency Flag (Rich Text)
```
If(
  [Is Urgent],
  "<span style='background:#E74C3C;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold'>⚡ URGENT</span>",
  ""
)
```

### Field: Summary Line (Text)
One-line summary for approval emails and Teams cards.
```
[Request Number] & " | " & [Title] & " | R" &
ToText(Round([Total Amount], 0)) & " | " & [Category] & " | " & [Status]
```

### Field: Days Since Submission (Numeric)
```
DateDiff(Now(), [Date Created], "days")
```

---

## Budget Codes Table

### Field: Available Budget (Numeric — Currency)
```
ToNumber([Annual Budget]) - ToNumber([Committed Amount]) - ToNumber([Spent Amount])
```

### Field: Utilization % (Numeric)
```
If(
  ToNumber([Annual Budget]) > 0,
  Round(
    (ToNumber([Committed Amount]) + ToNumber([Spent Amount])) /
    ToNumber([Annual Budget]) * 100,
    1
  ),
  0
)
```

### Field: Budget Status (Text)
```
If(
  [Utilization %] >= 100, "Overspent",
  If(
    [Utilization %] >= ToNumber([Budget Alert Threshold %]), "At Risk",
    "Healthy"
  )
)
```

### Field: Budget Status Color (Text)
```
Case(
  [Budget Status],
  "Healthy",   "#27AE60",
  "At Risk",   "#F39C12",
  "Overspent", "#E74C3C",
  "#95A5A6"
)
```

### Field: Remaining % (Numeric)
```
100 - [Utilization %]
```

---

## Purchase Orders Table

### Field: PO Number (Text)
```
"PO-" & Right("000000" & ToText([Record ID#]), 6)
```

### Field: Variance (Numeric — Currency)
Difference between PO amount and actual invoice amount. Negative = invoice higher than PO.
```
If(
  Not(IsNull([Invoice Amount])),
  ToNumber([PO Amount]) - ToNumber([Invoice Amount]),
  null()
)
```

### Field: Match Status (Text)
Three-way match indicator for invoice processing.
```
If(
  IsNull([Invoice Amount]), "Awaiting Invoice",
  If(
    Abs([Variance]) <= 100, "Matched",
    If(
      [Variance] < 0, "Invoice Over PO — Review Required",
      "Invoice Under PO"
    )
  )
)
```

### Field: Days to Pay (Numeric)
Days elapsed since invoice was received.
```
If(
  Not(IsNull([Invoice Date])) and [Status] <> "Paid",
  DateDiff(Now(), [Invoice Date], "days"),
  null()
)
```

---

## Approval History Table

### Field: Response Time Hours (Numeric)
```
If(
  Not(IsNull([Decision Date])) and Not(IsNull([Sent Date])),
  DateDiff([Decision Date], [Sent Date], "hours"),
  null()
)
```
