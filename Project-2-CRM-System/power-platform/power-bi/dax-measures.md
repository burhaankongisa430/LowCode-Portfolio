# Power BI — DAX Measures

Connect Power BI to Quickbase via REST API connector.
Load tables: Deals, Contacts, Companies, Activities, Sales Reps, Pipeline Stages.

---

## Pipeline Value Measures

### Total Pipeline Value (All Open Deals)
```dax
Pipeline Value =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Stage] <> "Closed Won",
    Deals[Stage] <> "Closed Lost"
)
```

### Weighted Pipeline Value
The statistically expected revenue across all open deals.

```dax
Weighted Pipeline Value =
CALCULATE(
    SUMX(Deals, Deals[Deal Value] * Deals[Win Probability %] / 100),
    Deals[Stage] <> "Closed Won",
    Deals[Stage] <> "Closed Lost"
)
```

### Pipeline by Stage
```dax
Pipeline by Stage =
CALCULATE(
    [Pipeline Value],
    ALLEXCEPT(Deals, Deals[Stage])
)
```

### Pipeline Coverage Ratio
Pipeline needed to hit quota — target is 3× for most B2B sales.

```dax
Pipeline Coverage Ratio =
DIVIDE(
    [Weighted Pipeline Value],
    SUM('Sales Reps'[Quota (Monthly)]),
    0
)
```

---

## Revenue Measures

### Won Revenue — Current Month
```dax
Won MTD =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Stage] = "Closed Won",
    DATESMTD(Deals[Actual Close Date])
)
```

### Won Revenue — Current Quarter
```dax
Won QTD =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Stage] = "Closed Won",
    DATESQTD(Deals[Actual Close Date])
)
```

### Won Revenue — Current Year
```dax
Won YTD =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Stage] = "Closed Won",
    DATESYTD(Deals[Actual Close Date])
)
```

### MoM Revenue Growth
```dax
Won Last Month =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Stage] = "Closed Won",
    DATEADD(DATESMTD(Deals[Actual Close Date]), -1, MONTH)
)

MoM Revenue Growth =
DIVIDE([Won MTD] - [Won Last Month], [Won Last Month], 0)
```

---

## Win Rate & Conversion Measures

### Win Rate (Overall)
```dax
Win Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Deals), Deals[Stage] = "Closed Won"),
    CALCULATE(COUNTROWS(Deals), Deals[Stage] IN {"Closed Won", "Closed Lost"}),
    0
)
```

### Win Rate by Lead Source
```dax
Win Rate by Source =
DIVIDE(
    CALCULATE(COUNTROWS(Deals), Deals[Stage] = "Closed Won"),
    CALCULATE(COUNTROWS(Deals), Deals[Stage] IN {"Closed Won", "Closed Lost"}),
    0
)
-- Apply in a visual with Lead Source on axis
```

### Average Deal Value — Won Deals
```dax
Avg Won Deal Value =
CALCULATE(
    AVERAGE(Deals[Deal Value]),
    Deals[Stage] = "Closed Won"
)
```

### Average Sales Cycle Days
```dax
Avg Sales Cycle =
AVERAGEX(
    FILTER(Deals, Deals[Stage] = "Closed Won"),
    Deals[Deal Age Days]
)
```

---

## Forecast Measures

### Commit Forecast
Deals with ≥ 85% win probability — these are counted in this month's commit.

```dax
Commit Forecast =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Forecast Category] = "Commit",
    Deals[Stage] <> "Closed Won",
    Deals[Stage] <> "Closed Lost"
)
```

### Best Case Forecast
```dax
Best Case Forecast =
CALCULATE(
    SUM(Deals[Weighted Value]),
    Deals[Forecast Category] IN {"Commit", "Best Case"},
    Deals[Stage] <> "Closed Won",
    Deals[Stage] <> "Closed Lost"
)
```

### Total Forecast (Won + Commit)
The most conservative revenue forecast.

```dax
Total Forecast =
[Won MTD] + [Commit Forecast]
```

### Forecast vs Quota
```dax
Forecast vs Quota =
DIVIDE([Total Forecast], SUM('Sales Reps'[Quota (Monthly)]), 0)
```

---

## Activity & Engagement Measures

### Total Activities Logged
```dax
Total Activities = COUNTROWS(Activities)
```

### Activities per Deal (Open)
```dax
Activities per Deal =
DIVIDE(
    COUNTROWS(Activities),
    CALCULATE(COUNTROWS(Deals), Deals[Stage] <> "Closed Won", Deals[Stage] <> "Closed Lost"),
    0
)
```

### Deals with No Recent Activity (> 14 days)
```dax
Stalled Deals =
CALCULATE(
    COUNTROWS(Deals),
    Deals[Deal Health Label] = "Stalled",
    Deals[Stage] <> "Closed Won",
    Deals[Stage] <> "Closed Lost"
)
```

### Avg Days Since Last Activity (Open Deals)
```dax
Avg Days Since Activity =
AVERAGEX(
    FILTER(Deals, Deals[Stage] <> "Closed Won" && Deals[Stage] <> "Closed Lost"),
    Deals[Days Since Last Activity]
)
```

---

## Loss Analysis Measures

### Loss Rate by Reason
```dax
Loss Rate by Reason =
DIVIDE(
    CALCULATE(COUNTROWS(Deals), Deals[Stage] = "Closed Lost"),
    CALCULATE(COUNTROWS(Deals), Deals[Stage] IN {"Closed Won", "Closed Lost"}),
    0
)
-- Apply in a visual with Loss Reason on axis
```

### Lost Revenue by Reason
```dax
Lost Revenue by Reason =
CALCULATE(
    SUM(Deals[Deal Value]),
    Deals[Stage] = "Closed Lost"
)
-- Apply in a visual with Loss Reason on axis
```

### Average Stage at Loss
```dax
Avg Stage at Loss =
AVERAGEX(
    FILTER(Deals, Deals[Stage] = "Closed Lost"),
    SWITCH(
        Deals[Previous Stage],
        "New Lead",      1,
        "Qualified",     2,
        "Proposal Sent", 3,
        "Negotiation",   4,
        "Verbal Commit", 5,
        0
    )
)
```

---

## Rep Performance Measures

### Quota Attainment (per Rep)
```dax
Quota Attainment =
DIVIDE(
    CALCULATE(SUM(Deals[Deal Value]), Deals[Stage] = "Closed Won", DATESMTD(Deals[Actual Close Date])),
    SELECTEDVALUE('Sales Reps'[Quota (Monthly)], 1),
    0
)
-- Apply in a table with Sales Rep on rows
```

### Rep Win Rate
```dax
Rep Win Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Deals), Deals[Stage] = "Closed Won"),
    CALCULATE(COUNTROWS(Deals), Deals[Stage] IN {"Closed Won", "Closed Lost"}),
    0
)
```

### Rep Pipeline Health Score
```dax
Rep Pipeline Health =
AVERAGEX(
    FILTER(Deals, Deals[Stage] <> "Closed Won" && Deals[Stage] <> "Closed Lost"),
    Deals[Deal Health Score]
)
```

---

## Conditional Formatting

### Win Rate RAG Color
```dax
Win Rate Color =
SWITCH(
    TRUE(),
    [Win Rate] >= 0.50, "#27AE60",
    [Win Rate] >= 0.30, "#F39C12",
    "#E74C3C"
)
```

### Forecast vs Quota Color
```dax
Forecast Color =
SWITCH(
    TRUE(),
    [Forecast vs Quota] >= 1.0, "#27AE60",
    [Forecast vs Quota] >= 0.75, "#F39C12",
    "#E74C3C"
)
```
