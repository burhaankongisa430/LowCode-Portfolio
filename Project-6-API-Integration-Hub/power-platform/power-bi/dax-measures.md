# Power BI — DAX Measures (API Integration Hub)

Connect to Quickbase via REST API. Load: Integration Events, Integration Routes, Dead Letter Queue, Integration Health.

---

## Volume Measures

### Total Events Today
```dax
Events Today =
CALCULATE(
    COUNTROWS('Integration Events'),
    'Integration Events'[Date Created] = TODAY()
)
```

### Total Events This Week
```dax
Events This Week =
CALCULATE(
    COUNTROWS('Integration Events'),
    DATESINPERIOD('Integration Events'[Date Created], TODAY(), -7, DAY)
)
```

### Events by Source (for bar chart)
```dax
Events by Source =
CALCULATE(COUNTROWS('Integration Events'))
-- Apply in visual with Source System on axis
```

### Event Volume WoW Change
```dax
Events Last Week =
CALCULATE(
    COUNTROWS('Integration Events'),
    DATESINPERIOD('Integration Events'[Date Created], TODAY() - 7, -7, DAY)
)

Event Volume WoW =
DIVIDE([Events This Week] - [Events Last Week], [Events Last Week], 0)
```

---

## Reliability Measures

### Overall Success Rate
```dax
Success Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Integration Events'), 'Integration Events'[Status] = "Success"),
    CALCULATE(COUNTROWS('Integration Events'), 'Integration Events'[Status] IN {"Success", "Failed", "Dead Letter"}),
    0
)
```

### Success Rate Today
```dax
Success Rate Today =
CALCULATE(
    [Success Rate],
    'Integration Events'[Date Created] = TODAY()
)
```

### Failure Count
```dax
Failed Events =
CALCULATE(
    COUNTROWS('Integration Events'),
    'Integration Events'[Status] IN {"Failed", "Dead Letter"}
)
```

### DLQ Rate
```dax
DLQ Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Integration Events'), 'Integration Events'[Status] = "Dead Letter"),
    COUNTROWS('Integration Events'),
    0
)
```

### Open DLQ Items
```dax
Open DLQ =
CALCULATE(
    COUNTROWS('Dead Letter Queue'),
    'Dead Letter Queue'[Status] = "Pending"
)
```

### DLQ Resolution Rate (last 30 days)
```dax
DLQ Resolution Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Dead Letter Queue'), 'Dead Letter Queue'[Status] = "Resolved"),
    CALCULATE(COUNTROWS('Dead Letter Queue'), 'Dead Letter Queue'[Status] IN {"Resolved", "Abandoned", "Pending"}),
    0
)
```

---

## Performance Measures

### Avg Processing Time (ms)
```dax
Avg Processing Ms =
AVERAGEX(
    FILTER('Integration Events', NOT(ISBLANK('Integration Events'[Processing Time ms]))),
    'Integration Events'[Processing Time ms]
)
```

### P95 Processing Time (ms)
Approximate P95 using PERCENTILEINC.
```dax
P95 Processing Ms =
PERCENTILEX.INC(
    FILTER('Integration Events', NOT(ISBLANK('Integration Events'[Processing Time ms]))),
    'Integration Events'[Processing Time ms],
    0.95
)
```

### Slowest Route (for ranking)
```dax
Avg Processing by Route =
CALCULATE([Avg Processing Ms])
-- Apply in table with Route ID on rows, sorted DESC
```

---

## Route Health Measures

### Active Routes
```dax
Active Routes =
CALCULATE(COUNTROWS('Integration Routes'), 'Integration Routes'[Is Active] = TRUE())
```

### Routes with Failures Today
```dax
Routes with Failures =
CALCULATE(
    COUNTROWS('Integration Routes'),
    'Integration Routes'[Failure Count Today] > 0
)
```

### Route Failure Rate (per route)
```dax
Route Failure Rate =
DIVIDE(
    SELECTEDVALUE('Integration Routes'[Failure Count Today]),
    SELECTEDVALUE('Integration Routes'[Event Count Today]),
    0
)
```

### Success Rate by Source System
```dax
Source Success Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Integration Events'), 'Integration Events'[Status] = "Success"),
    CALCULATE(COUNTROWS('Integration Events'), 'Integration Events'[Status] IN {"Success","Failed","Dead Letter"}),
    0
)
-- Apply in table with Source System on rows
```

---

## Retry Measures

### Total Retries (avg per event)
```dax
Avg Retries per Event =
AVERAGEX(
    FILTER('Integration Events', 'Integration Events'[Retry Count] > 0),
    'Integration Events'[Retry Count]
)
```

### Events Recovered via Retry
```dax
Events Recovered =
CALCULATE(
    COUNTROWS('Dead Letter Queue'),
    'Dead Letter Queue'[Status] = "Resolved"
)
```

---

## Conditional Formatting

### Success Rate RAG
```dax
Success Rate RAG =
SWITCH(
    TRUE(),
    [Success Rate Today] >= 0.95, "#27AE60",
    [Success Rate Today] >= 0.80, "#F39C12",
    "#E74C3C"
)
```

### DLQ Count Color
```dax
DLQ Color =
SWITCH(
    TRUE(),
    [Open DLQ] = 0, "#27AE60",
    [Open DLQ] <= 5, "#F39C12",
    "#E74C3C"
)
```
