# Quickbase Formula Fields

Unless noted, formulas apply to the **Employees** or **Onboarding Tasks** tables.

---

## Employees Table

### Field: Employee ID (Text)
```
"EMP-" & ToText([Record ID#])
```

### Field: Full Name (Text)
```
[First Name] & " " & [Last Name]
```

### Field: Days Until Start (Numeric)
Positive = start date is in the future. Negative = already started.
```
DateDiff([Start Date], Today(), "days")
```

### Field: Days Since Start (Numeric)
Positive = hire has started. Negative = not yet started.
```
DateDiff(Today(), [Start Date], "days")
```

### Field: Current Phase (Text)
Reflects which onboarding phase applies today based on days since start.
```
If(
  [Days Since Start] < 0,   "Pre-boarding",
  If(
    [Days Since Start] = 0, "Day 1",
    If(
      [Days Since Start] <= 5,  "Week 1",
      If(
        [Days Since Start] <= 30, "Month 1",
        If(
          [Days Since Start] <= 90, "90 Days",
          "Completed"
        )
      )
    )
  )
)
```

### Field: Overall Progress % (Numeric)
Requires two summary fields on the Employees table:
- `Total Tasks` = Count of related Onboarding Tasks records
- `Completed Tasks` = Count where Status = "Completed"

```
If(
  ToNumber([Total Tasks]) > 0,
  Round(ToNumber([Completed Tasks]) / ToNumber([Total Tasks]) * 100, 1),
  0
)
```

### Field: Onboarding Health (Text)
```
If(
  [Onboarding Status] = "Completed", "Completed",
  If(
    ToNumber([Overdue Tasks]) = 0, "On Track",
    If(
      ToNumber([Overdue Tasks]) <= 2, "At Risk",
      "Delayed"
    )
  )
)
```

### Field: Onboarding Health Color (Text)
```
Case(
  [Onboarding Health],
  "On Track",   "#27AE60",
  "At Risk",    "#F39C12",
  "Delayed",    "#E74C3C",
  "Completed",  "#2980B9",
  "#95A5A6"
)
```

### Field: Welcome Message (Rich Text)
Displayed on the new hire's Power Apps portal home screen.
```
"<h2>Welcome, " & [First Name] & "! 👋</h2>" &
"<p>Your onboarding is <b>" & ToText([Overall Progress %]) & "% complete</b>.</p>" &
"<p>Current phase: <b>" & [Current Phase] & "</b></p>" &
If(
  ToNumber([Overdue Tasks]) > 0,
  "<p style='color:#E74C3C;'><b>⚠ You have " & ToText([Overdue Tasks]) & " overdue task(s). Please action these today.</b></p>",
  "<p style='color:#27AE60;'>✅ You are on track. Keep it up!</p>"
)
```

### Field: Manager Notification Line (Text)
One-line status for manager digest emails.
```
[Full Name] & " | " & [Current Phase] & " | " &
ToText([Overall Progress %]) & "% complete | " &
ToText([Overdue Tasks]) & " overdue"
```

---

## Onboarding Tasks Table

### Field: Task ID (Text)
```
"TSK-" & ToText([Record ID#])
```

### Field: Is Overdue (Checkbox)
```
If(
  [Status] <> "Completed" and
  [Status] <> "N/A" and
  [Status] <> "Blocked" and
  Not(IsNull([Due Date])) and
  Today() > [Due Date],
  true(),
  false()
)
```

### Field: Days Until Due (Numeric)
Positive = days remaining. Negative = already past due date.
```
If(
  [Status] = "Completed" or [Status] = "N/A",
  null(),
  DateDiff([Due Date], Today(), "days")
)
```

### Field: Days Overdue (Numeric)
Only populated when the task is past its due date and not completed.
```
If(
  [Is Overdue],
  DateDiff(Today(), [Due Date], "days"),
  null()
)
```

### Field: Status Color (Text)
```
Case(
  [Status],
  "Completed",   "#27AE60",
  "In Progress", "#3498DB",
  "Overdue",     "#E74C3C",
  "Blocked",     "#9B59B6",
  "N/A",         "#95A5A6",
  "Not Started", "#BDC3C7",
  "#BDC3C7"
)
```

### Field: Phase Order (Numeric)
Used for sorting tasks in the correct chronological phase order.
```
Case(
  [Phase],
  "Pre-boarding", 1,
  "Day 1",        2,
  "Week 1",       3,
  "Month 1",      4,
  "90 Days",      5,
  99
)
```

### Field: Priority Label (Rich Text)
Highlights overdue tasks visually in reports.
```
If(
  [Is Overdue],
  "<span style='background:#E74C3C;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold'>OVERDUE</span>",
  If(
    [Days Until Due] = 0,
    "<span style='background:#F39C12;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold'>DUE TODAY</span>",
    If(
      [Days Until Due] <= 2,
      "<span style='background:#E67E22;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px'>DUE SOON</span>",
      ""
    )
  )
)
```

### Field: Owner Summary (Text)
Combines owner role and name for display in task lists.
```
"[" & [Owner Role] & "] " & If(IsNull([Owner Name]), "Unassigned", [Owner Name])
```

### Field: Completion Duration Days (Numeric)
How long the task took from creation to completion.
```
If(
  Not(IsNull([Completed Date])),
  DateDiff([Completed Date], [Date Created], "days"),
  null()
)
```

---

## Equipment Requests Table

### Field: Request ID (Text)
```
"EQR-" & ToText([Record ID#])
```

### Field: Days Until Required (Numeric)
```
If(
  [Status] = "Delivered",
  null(),
  DateDiff([Required By Date], Today(), "days")
)
```

### Field: Delivery Risk (Text)
```
If(
  [Status] = "Delivered" or [Status] = "Canceled",
  "N/A",
  If(
    [Days Until Required] < 0, "Late",
    If(
      [Days Until Required] <= 3, "At Risk",
      "On Track"
    )
  )
)
```
