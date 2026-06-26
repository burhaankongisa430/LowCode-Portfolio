# Power BI — DAX Measures (Transformation Impact Dashboard)

6-page workbook: Executive Summary, ROI Timeline, Domain Impact, Process Improvements, Milestone Tracker, Lessons Learned.

---

## Page 1: Executive Summary

### Overall ROI %
```dax
Overall ROI =
DIVIDE(
    SUM('ROI Measurements'[Actual Benefits YTD]) - MAX('ROI Measurements'[Total Investment]),
    MAX('ROI Measurements'[Total Investment]),
    0
) * 100
```

### Total Benefits YTD
```dax
Total Benefits YTD =
CALCULATE(
    SUM('ROI Measurements'[Actual Benefits YTD]),
    TOPN(1, 'ROI Monthly Snapshots', 'ROI Monthly Snapshots'[Snapshot Date], DESC)
)
```

### Net Present Value (3-Year)
```dax
NPV 3 Year =
VAR AnnualBenefit = SUM('ROI Measurements'[Actual Benefits Annual])
VAR AnnualOPEX    = SUM('ROI Measurements'[Annual OPEX])
VAR Investment    = MAX('ROI Measurements'[Total Investment])
VAR DiscountRate  = 0.10
RETURN
    -Investment +
    (AnnualBenefit - AnnualOPEX) / (1 + DiscountRate) +
    (AnnualBenefit - AnnualOPEX) / POWER(1 + DiscountRate, 2) +
    (AnnualBenefit - AnnualOPEX) / POWER(1 + DiscountRate, 3)
```

### Payback Period (Months)
```dax
Payback Months =
VAR MonthlyNetBenefit =
    DIVIDE(
        SUM('ROI Measurements'[Actual Benefits Annual]) -
        SUM('ROI Measurements'[Annual OPEX]),
        12,
        0
    )
VAR Investment = MAX('ROI Measurements'[Total Investment])
RETURN
IF(MonthlyNetBenefit > 0, DIVIDE(Investment, MonthlyNetBenefit, 0), BLANK())
```

### Benefit Realization Rate
```dax
Benefit Realization =
DIVIDE(
    SUM('ROI Measurements'[Actual Benefits YTD]),
    SUM('ROI Measurements'[Projected Benefits YTD]),
    0
) * 100
```

### Milestone Completion Rate
```dax
Milestone Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Milestones), Milestones[Status] = "Complete"),
    COUNTROWS(Milestones),
    0
) * 100
```

---

## Page 2: ROI Timeline

### Cumulative Actual Benefits (monthly trend)
```dax
Cumulative Actual Benefits =
CALCULATE(
    SUM('ROI Monthly Snapshots'[Actual Benefits]),
    FILTER(
        ALL('ROI Monthly Snapshots'),
        'ROI Monthly Snapshots'[Month Number] <= MAX('ROI Monthly Snapshots'[Month Number])
    )
)
```

### Cumulative Projected Benefits
```dax
Cumulative Projected Benefits =
CALCULATE(
    SUM('ROI Monthly Snapshots'[Projected Benefits]),
    FILTER(
        ALL('ROI Monthly Snapshots'),
        'ROI Monthly Snapshots'[Month Number] <= MAX('ROI Monthly Snapshots'[Month Number])
    )
)
```

### Break-Even Line (static reference line)
```dax
Investment Line =
MAX('ROI Measurements'[Total Investment])
-- Use as a constant line in the cumulative chart to show payback crossing point
```

### Month-over-Month Benefit Growth
```dax
MoM Benefit Growth =
VAR CurrentMonth = MAX('ROI Monthly Snapshots'[Actual Benefits])
VAR PriorMonth   = CALCULATE(
    SUM('ROI Monthly Snapshots'[Actual Benefits]),
    DATEADD('ROI Monthly Snapshots'[Snapshot Date], -1, MONTH)
)
RETURN DIVIDE(CurrentMonth - PriorMonth, PriorMonth, 0)
```

---

## Page 3: Domain Impact

### Domain ROI by Initiative
```dax
Domain ROI =
DIVIDE(
    [Domain Actual Benefits] - SELECTEDVALUE(Initiatives[Investment]),
    SELECTEDVALUE(Initiatives[Investment]),
    0
) * 100
-- Apply in a bar chart with Initiative Name on axis
```

### Domain Actual Benefits
```dax
Domain Actual Benefits =
CALCULATE(SUM('ROI Measurements'[Actual Benefits Annual]))
-- Apply filtered by Initiative
```

### Hours Saved (all domains)
```dax
Total Hours Saved =
SUM('Process Baselines'[Hours Saved Annual])
```

### FTE Equivalent Saved
```dax
FTE Equivalent =
DIVIDE([Total Hours Saved], 2080, 0)
-- 2080 = standard annual working hours (52 × 40h)
```

---

## Page 4: Process Improvements

### Avg Improvement % (all KPIs)
```dax
Avg Improvement =
AVERAGEX(
    'Process Baselines',
    'Process Baselines'[Improvement %]
)
```

### KPIs On Target
```dax
KPIs On Target =
CALCULATE(
    COUNTROWS('Process Baselines'),
    'Process Baselines'[Target Met] = TRUE()
)
```

### KPI Target Rate
```dax
KPI Target Rate =
DIVIDE([KPIs On Target], COUNTROWS('Process Baselines'), 0) * 100
```

### Biggest Win (max improvement)
```dax
Biggest Improvement =
MAXX('Process Baselines', 'Process Baselines'[Improvement %])
```

### Before vs After by Metric (for table visual)
```dax
Before Value = SELECTEDVALUE('Process Baselines'[Before Value])
After Value  = SELECTEDVALUE('Process Baselines'[After Value])
Improvement  = SELECTEDVALUE('Process Baselines'[Improvement %])
```

---

## Page 5: Milestone Tracker

### Completed Milestones
```dax
Completed Milestones =
CALCULATE(COUNTROWS(Milestones), Milestones[Status] = "Complete")
```

### Overdue Milestones
```dax
Overdue Milestones =
CALCULATE(
    COUNTROWS(Milestones),
    Milestones[Status] <> "Complete",
    Milestones[Planned Date] < TODAY()
)
```

### Average Schedule Variance (days)
```dax
Avg Schedule Variance =
AVERAGEX(
    FILTER(Milestones, Milestones[Status] = "Complete"),
    Milestones[Days Variance]
)
-- Positive = delivered late; Negative = delivered early
```

### On-Time Delivery Rate
```dax
On Time Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Milestones), Milestones[Status] = "Complete", Milestones[Days Variance] <= 0),
    CALCULATE(COUNTROWS(Milestones), Milestones[Status] = "Complete"),
    0
) * 100
```

---

## Conditional Formatting

### ROI RAG
```dax
ROI Color =
SWITCH(
    TRUE(),
    [Overall ROI] >= 200, "#27AE60",
    [Overall ROI] >= 100, "#2ECC71",
    [Overall ROI] >= 50,  "#F39C12",
    "#E74C3C"
)
```

### Benefit Realization RAG
```dax
Realization Color =
SWITCH(
    TRUE(),
    [Benefit Realization] >= 100, "#1ABC9C",
    [Benefit Realization] >= 85,  "#27AE60",
    [Benefit Realization] >= 70,  "#F39C12",
    "#E74C3C"
)
```
