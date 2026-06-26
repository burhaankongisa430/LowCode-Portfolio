# Power BI — DAX Measures (Executive Dashboard)

Connect to Dataverse via the native connector in DirectQuery mode.
Tables: KPI_Snapshot, KPI_Alert.
Also import directly from each QB app for domain-specific pages.

---

## Page 1: Executive Summary

### Current Health Score
```dax
Current Health Score =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_health_score]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Health Score Label
```dax
Health Score Label =
VAR Score = [Current Health Score]
RETURN
SWITCH(
    TRUE(),
    Score >= 85, "Excellent",
    Score >= 70, "Good",
    Score >= 55, "Needs Attention",
    Score >= 40, "At Risk",
    "Critical"
)
```

### Health Score Color
```dax
Health Score Color =
VAR Score = [Current Health Score]
RETURN
SWITCH(
    TRUE(),
    Score >= 85, "#27AE60",
    Score >= 70, "#2ECC71",
    Score >= 55, "#F39C12",
    Score >= 40, "#E67E22",
    "#E74C3C"
)
```

### Current Operational Score
```dax
Current Operational Score =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_operational_score]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Current Commercial Score
```dax
Current Commercial Score =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_commercial_score]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Current People Score
```dax
Current People Score =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_people_score]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Current Finance Score
```dax
Current Finance Score =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_finance_score]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Health Score WoW Change
```dax
Health Score WoW =
VAR CurrentScore =
    CALCULATE(
        AVERAGE(KPI_Snapshot[cr_health_score]),
        KPI_Snapshot[cr_snapshot_time] >= NOW() - 1
    )
VAR LastWeekScore =
    CALCULATE(
        AVERAGE(KPI_Snapshot[cr_health_score]),
        KPI_Snapshot[cr_snapshot_time] >= NOW() - 8 &&
        KPI_Snapshot[cr_snapshot_time] < NOW() - 7
    )
RETURN CurrentScore - LastWeekScore
```

### Active Alert Count
```dax
Active Alerts =
CALCULATE(
    COUNTROWS(KPI_Alert),
    KPI_Alert[cr_alert_time] >= NOW() - 1,
    KPI_Alert[cr_acknowledged] = FALSE()
)
```

### Critical Alert Count
```dax
Critical Alerts =
CALCULATE(
    COUNTROWS(KPI_Alert),
    KPI_Alert[cr_severity] = "Critical",
    KPI_Alert[cr_alert_time] >= NOW() - 1
)
```

---

## Page 1: Trend Analysis (Shared Timeline)

### 7-Day Average Health Score
```dax
Avg Health 7D =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_health_score]),
    DATESINPERIOD(KPI_Snapshot[cr_snapshot_time], NOW(), -7, DAY)
)
```

### 30-Day Average Health Score
```dax
Avg Health 30D =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_health_score]),
    DATESINPERIOD(KPI_Snapshot[cr_snapshot_time], NOW(), -30, DAY)
)
```

### Health Score Trend (daily rolling average for sparkline)
```dax
Daily Health Score =
AVERAGEX(
    VALUES(KPI_Snapshot[Snapshot_Date]),
    CALCULATE(AVERAGE(KPI_Snapshot[cr_health_score]))
)
-- Apply in a line chart with Snapshot_Date on the X axis
```

---

## Page 2: Operational (Service Desk)

### Current SLA Met Rate
```dax
Current SLA Met Rate =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_sla_met_rate]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### SLA Rate vs Target (95% target)
```dax
SLA Rate Gap =
[Current SLA Met Rate] - 95
-- Negative = below target
```

### Current Active Breaches
```dax
Current Active Breaches =
CALCULATE(
    SUM(KPI_Snapshot[cr_active_breaches]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Breach Trend (7-day)
```dax
Avg Breaches 7D =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_active_breaches]),
    DATESINPERIOD(KPI_Snapshot[cr_snapshot_time], NOW(), -7, DAY)
)
```

### Current Avg Resolution Hours
```dax
Current Avg Resolution Hours =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_avg_resolution_hours]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

---

## Page 3: Commercial (Sales)

### Current Weighted Pipeline
```dax
Current Weighted Pipeline =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_weighted_pipeline]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Current Win Rate
```dax
Current Win Rate =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_win_rate]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Win Rate vs Target (35% target)
```dax
Win Rate Gap =
[Current Win Rate] - 35
```

### Current Quota Attainment
```dax
Current Quota Attainment =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_quota_attainment]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Won Revenue MTD (Latest)
```dax
Won Revenue MTD =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_won_revenue_mtd]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Stalled Deals Count
```dax
Current Stalled Deals =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_stalled_deals]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

---

## Page 4: People (HR & Onboarding)

### Current On Track Rate
```dax
Current On Track Rate =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_onboarding_on_track]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Day 1 Readiness Rate
```dax
Current Day1 Readiness =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_day1_readiness_rate]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Avg Completion Days Trend
```dax
Completion Days Trend =
AVERAGEX(
    VALUES(KPI_Snapshot[Snapshot_Date]),
    CALCULATE(AVERAGE(KPI_Snapshot[cr_avg_completion_days]))
)
```

---

## Page 5: Finance (Procurement)

### Current Budget Utilization
```dax
Current Budget Util =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_avg_budget_util]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Budget Utilization RAG
```dax
Budget Util RAG =
VAR Util = [Current Budget Util]
RETURN
SWITCH(
    TRUE(),
    Util >= 100, "#E74C3C",
    Util >= 85,  "#F39C12",
    "#27AE60"
)
```

### Current Approval Cycle Days
```dax
Current Approval Cycle =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_approval_cycle_days]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

### Pending Approvals
```dax
Current Pending Approvals =
CALCULATE(
    AVERAGE(KPI_Snapshot[cr_pending_approvals]),
    TOPN(1, KPI_Snapshot, KPI_Snapshot[cr_snapshot_time], DESC)
)
```

---

## Page 6: Cross-Domain Correlations

### Ops vs Commercial Correlation (for scatter)
-- Apply Operational Score on X axis, Commercial Score on Y axis
-- Each point = one daily snapshot
-- Reveals: does service desk performance correlate with sales performance?
```dax
-- No measure needed; use cr_operational_score and cr_commercial_score
-- as X/Y values in a scatter plot with cr_snapshot_time as the detail field
```

### Domain Divergence (how far domains diverge from each other)
```dax
Domain Divergence =
VAR Scores = {[Current Operational Score], [Current Commercial Score], [Current People Score], [Current Finance Score]}
VAR MaxScore = MAXX(Scores, [Value])
VAR MinScore = MINX(Scores, [Value])
RETURN MaxScore - MinScore
-- High divergence = systemic issue in one domain dragging overall score
```

### Alert Frequency by Domain (last 30 days)
```dax
Alert Frequency =
COUNTROWS(
    FILTER(KPI_Alert,
           KPI_Alert[cr_alert_time] >= NOW() - 30)
)
-- Apply in a bar chart with cr_domain on axis
```

---

## Conditional Formatting (Cross-Page)

### Universal Domain Score Color
```dax
Domain Score Color =
VAR Score = SELECTEDVALUE(KPI_Snapshot[cr_health_score])
RETURN
SWITCH(
    TRUE(),
    Score >= 85, "#27AE60",
    Score >= 70, "#2ECC71",
    Score >= 55, "#F39C12",
    Score >= 40, "#E67E22",
    "#E74C3C"
)
```
