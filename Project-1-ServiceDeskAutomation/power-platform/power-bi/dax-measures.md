# Power BI — DAX Measures

Connect Power BI to Quickbase via the REST API connector or export to CSV/Dataverse.
Apply these measures to the **Tickets** fact table.

---

## Core KPI Measures

### Total Open Tickets
```dax
Open Tickets =
CALCULATE(
    COUNTROWS(Tickets),
    Tickets[Status] <> "Resolved",
    Tickets[Status] <> "Closed"
)
```

### Total Tickets (All Time)
```dax
Total Tickets = COUNTROWS(Tickets)
```

### SLA Met Rate
```dax
SLA Met Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Tickets), Tickets[SLA Status] = "Met"),
    CALCULATE(COUNTROWS(Tickets), Tickets[Status] IN {"Resolved", "Closed"}),
    0
)
```

### SLA Breach Rate
```dax
SLA Breach Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Tickets), Tickets[SLA Status] = "Breached"),
    CALCULATE(COUNTROWS(Tickets), Tickets[Status] IN {"Resolved", "Closed"}),
    0
)
```

### Active Breaches
```dax
Active Breaches =
CALCULATE(
    COUNTROWS(Tickets),
    Tickets[SLA Status] = "Breached",
    Tickets[Status] <> "Resolved",
    Tickets[Status] <> "Closed"
)
```

### At Risk Tickets
```dax
At Risk Tickets =
CALCULATE(
    COUNTROWS(Tickets),
    Tickets[SLA Status] = "At Risk",
    Tickets[Status] <> "Resolved",
    Tickets[Status] <> "Closed"
)
```

---

## Resolution Time Measures

### Avg Resolution Time (Hours)
```dax
Avg Resolution Hours =
AVERAGEX(
    FILTER(Tickets, NOT(ISBLANK(Tickets[Resolution Time Hours]))),
    Tickets[Resolution Time Hours]
)
```

### Median Resolution Time (Hours)
```dax
Median Resolution Hours =
MEDIANX(
    FILTER(Tickets, NOT(ISBLANK(Tickets[Resolution Time Hours]))),
    Tickets[Resolution Time Hours]
)
```

### Avg Resolution by Priority
```dax
Avg Resolution P1 =
CALCULATE(
    [Avg Resolution Hours],
    Tickets[Priority] = "P1-Critical"
)

Avg Resolution P2 =
CALCULATE(
    [Avg Resolution Hours],
    Tickets[Priority] = "P2-High"
)
```

### Resolution Time vs SLA Target
```dax
Resolution vs SLA =
AVERAGEX(
    FILTER(Tickets, NOT(ISBLANK(Tickets[Resolution Time Hours]))),
    Tickets[Resolution Time Hours] - Tickets[Resolution SLA Hours]
)
-- Negative = under SLA (good), Positive = over SLA (breach)
```

---

## Volume Measures

### Tickets Created Today
```dax
Tickets Today =
CALCULATE(
    COUNTROWS(Tickets),
    Tickets[Date Created] = TODAY()
)
```

### Tickets Created This Week
```dax
Tickets This Week =
CALCULATE(
    COUNTROWS(Tickets),
    DATESINPERIOD(Tickets[Date Created], TODAY(), -7, DAY)
)
```

### Tickets Created Last Week (for WoW comparison)
```dax
Tickets Last Week =
CALCULATE(
    COUNTROWS(Tickets),
    DATESINPERIOD(Tickets[Date Created], TODAY() - 7, -7, DAY)
)
```

### Week-over-Week Volume Change
```dax
WoW Volume Change =
DIVIDE(
    [Tickets This Week] - [Tickets Last Week],
    [Tickets Last Week],
    0
)
```

---

## Agent Performance Measures

### Tickets Resolved per Agent
```dax
Tickets Resolved per Agent =
DIVIDE(
    CALCULATE(COUNTROWS(Tickets), Tickets[Status] IN {"Resolved", "Closed"}),
    DISTINCTCOUNT(Tickets[Assigned Agent])
)
```

### Agent SLA Met Rate
```dax
Agent SLA Met Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Tickets), Tickets[SLA Status] = "Met"),
    CALCULATE(COUNTROWS(Tickets), Tickets[Status] IN {"Resolved", "Closed"}),
    0
)
-- Apply this in a visual filtered by Assigned Agent
```

### First Response Within SLA
```dax
First Response Met =
CALCULATE(
    COUNTROWS(Tickets),
    NOT(ISBLANK(Tickets[First Response Date])),
    Tickets[First Response Date] <= Tickets[First Response Due]
)

First Response SLA Rate =
DIVIDE(
    [First Response Met],
    CALCULATE(COUNTROWS(Tickets), NOT(ISBLANK(Tickets[First Response Date]))),
    0
)
```

---

## Priority Distribution

### P1 Breach Rate
```dax
P1 Breach Rate =
CALCULATE(
    [SLA Breach Rate],
    Tickets[Priority] = "P1-Critical"
)
```

### Priority Mix %
```dax
Priority Mix % =
DIVIDE(COUNTROWS(Tickets), CALCULATE(COUNTROWS(Tickets), ALL(Tickets[Priority])), 0)
-- Apply in a visual with Priority on axis
```

---

## Time Intelligence

### Rolling 30-Day Breach Count
```dax
Breaches Last 30 Days =
CALCULATE(
    COUNTROWS(Tickets),
    Tickets[SLA Status] = "Breached",
    DATESINPERIOD(Tickets[Date Created], LASTDATE(Tickets[Date Created]), -30, DAY)
)
```

### MoM Resolution Improvement
```dax
Avg Resolution This Month =
CALCULATE(
    [Avg Resolution Hours],
    DATESMTD(Tickets[Date Created])
)

Avg Resolution Last Month =
CALCULATE(
    [Avg Resolution Hours],
    DATEADD(DATESMTD(Tickets[Date Created]), -1, MONTH)
)

MoM Resolution Improvement =
DIVIDE(
    [Avg Resolution Last Month] - [Avg Resolution This Month],
    [Avg Resolution Last Month],
    0
)
-- Positive = improving (faster)
```

---

## Conditional Formatting

### KPI Card Color (SLA Met Rate)
```dax
SLA Met Rate Color =
SWITCH(
    TRUE(),
    [SLA Met Rate] >= 0.95, "#27AE60",
    [SLA Met Rate] >= 0.85, "#F39C12",
    "#E74C3C"
)
```

### Active Breach Alert Color
```dax
Breach Alert Color =
IF([Active Breaches] > 0, "#E74C3C", "#27AE60")
```
