# Power BI — DAX Measures

Connect Power BI to Quickbase via REST API. Load: Employees, Onboarding Tasks, Departments, Equipment Requests.

---

## Onboarding Status Measures

### Active Hires
```dax
Active Hires =
CALCULATE(
    COUNTROWS(Employees),
    Employees[Onboarding Status] IN {"Active", "Pre-boarding"}
)
```

### Completed This Month
```dax
Completed This Month =
CALCULATE(
    COUNTROWS(Employees),
    Employees[Onboarding Status] = "Completed",
    DATESMTD(Employees[Date Created])
)
```

### On Track Rate
```dax
On Track Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Employees), Employees[Onboarding Health] = "On Track",
              Employees[Onboarding Status] IN {"Active", "Pre-boarding"}),
    [Active Hires],
    0
)
```

### At Risk or Delayed Rate
```dax
At Risk Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Employees),
              Employees[Onboarding Health] IN {"At Risk", "Delayed"},
              Employees[Onboarding Status] IN {"Active", "Pre-boarding"}),
    [Active Hires],
    0
)
```

### Average Progress % (Active Hires)
```dax
Avg Progress =
CALCULATE(
    AVERAGE(Employees[Overall Progress %]),
    Employees[Onboarding Status] IN {"Active", "Pre-boarding"}
)
```

---

## Time-to-Productivity Measures

### Average Days to Complete Onboarding
```dax
Avg Days to Complete =
AVERAGEX(
    FILTER(Employees, Employees[Onboarding Status] = "Completed"),
    Employees[Days Since Start]
)
```

### Median Days to Complete
```dax
Median Days to Complete =
MEDIANX(
    FILTER(Employees, Employees[Onboarding Status] = "Completed"),
    Employees[Days Since Start]
)
```

### MoM Improvement in Completion Time
```dax
Completion Time This Month =
CALCULATE([Avg Days to Complete], DATESMTD(Employees[Date Created]))

Completion Time Last Month =
CALCULATE(
    [Avg Days to Complete],
    DATEADD(DATESMTD(Employees[Date Created]), -1, MONTH)
)

MoM Completion Improvement =
DIVIDE([Completion Time Last Month] - [Completion Time This Month],
       [Completion Time Last Month], 0)
-- Positive = improving (faster completion)
```

---

## Task Measures

### Total Tasks Created
```dax
Total Tasks = COUNTROWS('Onboarding Tasks')
```

### Overdue Tasks (Open)
```dax
Overdue Tasks =
CALCULATE(
    COUNTROWS('Onboarding Tasks'),
    'Onboarding Tasks'[Is Overdue] = TRUE(),
    'Onboarding Tasks'[Status] <> "Completed"
)
```

### Task Completion Rate
```dax
Task Completion Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Onboarding Tasks'), 'Onboarding Tasks'[Status] = "Completed"),
    COUNTROWS('Onboarding Tasks'),
    0
)
```

### Avg Tasks per Hire
```dax
Avg Tasks per Hire =
DIVIDE(COUNTROWS('Onboarding Tasks'), DISTINCTCOUNT('Onboarding Tasks'[Employee ID]), 0)
```

### Tasks by Owner Role
```dax
Tasks by Role =
CALCULATE(COUNTROWS('Onboarding Tasks'))
-- Apply in a visual with Owner Role on axis
```

### Overdue by Phase
```dax
Overdue by Phase =
CALCULATE(
    COUNTROWS('Onboarding Tasks'),
    'Onboarding Tasks'[Is Overdue] = TRUE()
)
-- Apply in a visual with Phase on axis
```

---

## Day 1 Readiness Measures

### Day 1 Access Ready Rate
Percentage of hires whose AD account and M365 license were provisioned before start date.

```dax
Day 1 Ready Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS(Employees),
        Employees[AD Account Created] = TRUE(),
        Employees[M365 License Assigned] = TRUE()
    ),
    COUNTROWS(Employees),
    0
)
```

### Equipment On-Time Delivery Rate
```dax
Equipment On Time =
DIVIDE(
    CALCULATE(
        COUNTROWS('Equipment Requests'),
        'Equipment Requests'[Delivery Risk] = "On Track",
        'Equipment Requests'[Status] = "Delivered"
    ),
    CALCULATE(COUNTROWS('Equipment Requests'), 'Equipment Requests'[Status] = "Delivered"),
    0
)
```

---

## Department Breakdown

### Hires by Department
```dax
Hires by Department = COUNTROWS(Employees)
-- Apply in a visual with Department Name on axis
```

### On Track Rate by Department
```dax
Dept On Track Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Employees), Employees[Onboarding Health] = "On Track"),
    COUNTROWS(Employees),
    0
)
-- Apply in a table with Department on rows
```

### Avg Completion Days by Department
```dax
Dept Avg Completion =
CALCULATE([Avg Days to Complete])
-- Apply in visual with Department on axis
```

---

## Conditional Formatting

### On Track Rate Color
```dax
On Track Color =
SWITCH(
    TRUE(),
    [On Track Rate] >= 0.90, "#27AE60",
    [On Track Rate] >= 0.75, "#F39C12",
    "#E74C3C"
)
```

### Overdue Count Color
```dax
Overdue Color =
IF([Overdue Tasks] = 0, "#27AE60", "#E74C3C")
```
