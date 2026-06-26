# Quickbase Formula Fields

All formulas are applied to the **Tickets** table unless otherwise noted.

---

## Field: Ticket ID (Text Formula)
Generates a human-readable ticket reference number.

```
"TKT-" & ToText([Record ID#])
```

---

## Field: Due Date (Date/Time Formula)
Calculates the SLA resolution deadline based on ticket priority.

```
If(
  [Priority] = "P1-Critical",
  DateAdd([Date Created], 4, "hours"),
  If(
    [Priority] = "P2-High",
    DateAdd([Date Created], 8, "hours"),
    If(
      [Priority] = "P3-Medium",
      DateAdd([Date Created], 24, "hours"),
      If(
        [Priority] = "P4-Low",
        DateAdd([Date Created], 72, "hours"),
        DateAdd([Date Created], 24, "hours")
      )
    )
  )
)
```

---

## Field: First Response Due (Date/Time Formula)
Calculates the SLA first-response deadline.

```
If(
  [Priority] = "P1-Critical",
  DateAdd([Date Created], 1, "hours"),
  If(
    [Priority] = "P2-High",
    DateAdd([Date Created], 4, "hours"),
    If(
      [Priority] = "P3-Medium",
      DateAdd([Date Created], 8, "hours"),
      DateAdd([Date Created], 24, "hours")
    )
  )
)
```

---

## Field: Response SLA Hours (Numeric Formula)
Returns the numeric SLA response time for use in reports and calculations.

```
Case(
  [Priority],
  "P1-Critical", 1,
  "P2-High", 4,
  "P3-Medium", 8,
  "P4-Low", 24,
  24
)
```

---

## Field: Resolution SLA Hours (Numeric Formula)
Returns the numeric SLA resolution time for use in reports and calculations.

```
Case(
  [Priority],
  "P1-Critical", 4,
  "P2-High", 8,
  "P3-Medium", 24,
  "P4-Low", 72,
  72
)
```

---

## Field: SLA Status (Text Formula)
Computes whether the ticket is On Track, At Risk, Breached, or Met.

```
If(
  Not(IsNull([Resolution Date])),
  If(
    [Resolution Date] <= [Due Date],
    "Met",
    "Breached"
  ),
  If(
    Now() > [Due Date],
    "Breached",
    If(
      Now() > DateAdd([Due Date], ToNumber([Resolution SLA Hours]) * -0.15, "hours"),
      "At Risk",
      "On Track"
    )
  )
)
```

*Note: "At Risk" triggers when less than 15% of SLA time remains.*

---

## Field: SLA Color (Text Formula)
Returns a hex color code for use in Quickbase rich text fields and dashboards.

```
Case(
  [SLA Status],
  "On Track",  "#27AE60",
  "At Risk",   "#F39C12",
  "Breached",  "#E74C3C",
  "Met",       "#2980B9",
  "#95A5A6"
)
```

---

## Field: Time Remaining Hours (Numeric Formula)
Returns hours remaining until SLA breach. Negative = already breached.

```
If(
  IsNull([Resolution Date]),
  DateDiff([Due Date], Now(), "hours"),
  null()
)
```

---

## Field: Resolution Time Hours (Numeric Formula)
Calculates actual resolution time in hours for closed tickets.

```
If(
  Not(IsNull([Resolution Date])),
  DateDiff([Resolution Date], [Date Created], "hours"),
  null()
)
```

---

## Field: Ticket Age Days (Numeric Formula)
Computes how long a ticket has been open (or its lifetime if closed).

```
DateDiff(
  If(
    IsNull([Resolution Date]),
    Now(),
    [Resolution Date]
  ),
  [Date Created],
  "days"
)
```

---

## Field: Is Overdue (Checkbox Formula)
Boolean flag for filtering and alerts.

```
If(
  IsNull([Resolution Date]) and Now() > [Due Date],
  true(),
  false()
)
```

---

## Field: Routing Team (Text Formula)
Automatically assigns the responsible team based on ticket category.

```
Case(
  [Category],
  "IT-Hardware",      "IT Support",
  "IT-Software",      "IT Support",
  "IT-Network",       "IT Support",
  "HR-Leave",         "HR",
  "HR-Payroll",       "HR",
  "HR-Benefits",      "HR",
  "Finance-Invoice",  "Finance",
  "Finance-Expense",  "Finance",
  "Facilities",       "Facilities",
  "IT Support"
)
```

---

## Field: Priority Badge (Rich Text Formula)
Generates a color-coded priority label for reports and forms.

```
"<span style='background-color:" &
  Case(
    [Priority],
    "P1-Critical", "#E74C3C",
    "P2-High",     "#E67E22",
    "P3-Medium",   "#F1C40F",
    "P4-Low",      "#27AE60",
    "#95A5A6"
  )
  & ";color:#fff;padding:2px 8px;border-radius:3px;font-weight:bold;'>" &
  [Priority] & "</span>"
```

---

## Field: Status Progress (Numeric Formula)
Maps status to a 0–100 progress value for timeline visualisation.

```
Case(
  [Status],
  "New",         0,
  "Assigned",    20,
  "In Progress", 50,
  "Pending",     70,
  "Resolved",    90,
  "Closed",      100,
  0
)
```

---

## Agents Table: Workload Status (Text Formula)
Placed on the **Agents** table to reflect current load.

```
If(
  [Is Active] = false(),
  "Inactive",
  If(
    [Active Ticket Count] >= [Max Capacity],
    "At Capacity",
    If(
      ToNumber([Active Ticket Count]) >= ToNumber([Max Capacity]) * 0.8,
      "Near Capacity",
      "Available"
    )
  )
)
```

---

## Agents Table: Capacity Percentage (Numeric Formula)

```
If(
  ToNumber([Max Capacity]) > 0,
  Round((ToNumber([Active Ticket Count]) / ToNumber([Max Capacity])) * 100, 0),
  0
)
```

---

## Knowledge Base: Helpfulness Rate (Numeric Formula)

```
If(
  ToNumber([Helpful Votes]) + ToNumber([Not Helpful Votes]) > 0,
  Round(
    (ToNumber([Helpful Votes]) / (ToNumber([Helpful Votes]) + ToNumber([Not Helpful Votes]))) * 100,
    1
  ),
  null()
)
```

---

## Ticket: Escalation Level (Text Formula)
Determines current escalation tier — used by Power Automate SLA flow.

```
If(
  IsNull([Resolution Date]) and Not(IsNull([Due Date])),
  If(
    Now() > [Due Date],
    "L2-Manager",
    If(
      [Priority] = "P1-Critical" and Now() > DateAdd([Date Created], 3, "hours"),
      "L2-Manager",
      If(
        [Priority] = "P1-Critical" and Now() > DateAdd([Date Created], 2, "hours"),
        "L1-TeamLead",
        If(
          [Priority] = "P2-High" and Now() > DateAdd([Date Created], 7, "hours"),
          "L2-Manager",
          If(
            [Priority] = "P2-High" and Now() > DateAdd([Date Created], 6, "hours"),
            "L1-TeamLead",
            "None"
          )
        )
      )
    )
  ),
  "None"
)
```

---

## Ticket: Summary Line (Text Formula)
One-line summary for notifications and Teams cards.

```
"[" & [Priority] & "] " & [Ticket ID] & " – " & [Title] &
" | " & [Status] & " | SLA: " & [SLA Status]
```
