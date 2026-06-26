# Power BI — DAX Measures

Connect Power BI to Quickbase via REST API.
Load tables: Purchase Requests, Vendors, Budget Codes, Approval History, Purchase Orders.

---

## Spend Measures

### Total Committed Spend (Open Requests)
```dax
Committed Spend =
CALCULATE(
    SUM('Purchase Requests'[Total Amount]),
    'Purchase Requests'[Status] NOT IN {"Rejected", "Canceled", "Draft"}
)
```

### Total Approved & PO Issued
```dax
Approved Spend =
CALCULATE(
    SUM('Purchase Requests'[Total Amount]),
    'Purchase Requests'[Status] IN {"Approved", "PO Issued"}
)
```

### Spend MTD
```dax
Spend MTD =
CALCULATE(
    SUM('Purchase Requests'[Total Amount]),
    'Purchase Requests'[Status] IN {"Approved", "PO Issued"},
    DATESMTD('Purchase Requests'[Date Created])
)
```

### Spend YTD
```dax
Spend YTD =
CALCULATE(
    SUM('Purchase Requests'[Total Amount]),
    'Purchase Requests'[Status] IN {"Approved", "PO Issued"},
    DATESYTD('Purchase Requests'[Date Created])
)
```

### Total Budget Available (All Departments)
```dax
Total Available Budget =
SUMX('Budget Codes', 'Budget Codes'[Available Budget])
```

### Budget Utilization Rate
```dax
Budget Utilization =
DIVIDE(
    CALCULATE(SUM('Budget Codes'[Committed Amount]) + SUM('Budget Codes'[Spent Amount])),
    SUM('Budget Codes'[Annual Budget]),
    0
)
```

### Over-Budget Requests
```dax
Over Budget Requests =
CALCULATE(
    COUNTROWS('Purchase Requests'),
    'Purchase Requests'[Budget Warning] = TRUE()
)
```

---

## Volume & Pipeline Measures

### Total Requests Submitted
```dax
Total Requests = COUNTROWS('Purchase Requests')
```

### Pending Approvals
```dax
Pending Approvals =
CALCULATE(
    COUNTROWS('Purchase Requests'),
    'Purchase Requests'[Status] IN {
        "Level 1 Pending","Level 2 Pending","Level 3 Pending","Level 4 Pending"
    }
)
```

### Approval Rate
```dax
Approval Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Purchase Requests'),
              'Purchase Requests'[Status] IN {"Approved","PO Issued"}),
    CALCULATE(COUNTROWS('Purchase Requests'),
              'Purchase Requests'[Status] IN {"Approved","PO Issued","Rejected"}),
    0
)
```

### Rejection Rate by Level
```dax
Rejection Rate by Level =
DIVIDE(
    CALCULATE(COUNTROWS('Approval History'), 'Approval History'[Decision] = "Rejected"),
    COUNTROWS('Approval History'),
    0
)
-- Apply in a visual with Approval Level on axis
```

---

## Cycle Time Measures

### Avg Approval Cycle Time (Days)
From submission to final decision (approved or rejected).

```dax
Avg Approval Cycle Days =
AVERAGEX(
    FILTER(
        'Purchase Requests',
        'Purchase Requests'[Status] IN {"Approved","PO Issued","Rejected"}
    ),
    'Purchase Requests'[Days Since Submission]
)
```

### Avg Response Time per Level (Hours)
```dax
Avg Response Time Hours =
AVERAGEX(
    FILTER('Approval History', NOT(ISBLANK('Approval History'[Response Time Hours]))),
    'Approval History'[Response Time Hours]
)
-- Apply in a table with Approval Level on rows
```

### SLA Breach Count
```dax
SLA Breaches =
CALCULATE(
    COUNTROWS('Purchase Requests'),
    'Purchase Requests'[SLA Breached] = TRUE()
)
```

### SLA Compliance Rate
```dax
SLA Compliance Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Purchase Requests'),
              'Purchase Requests'[SLA Breached] = FALSE(),
              'Purchase Requests'[Status] IN {"Approved","PO Issued","Rejected"}),
    CALCULATE(COUNTROWS('Purchase Requests'),
              'Purchase Requests'[Status] IN {"Approved","PO Issued","Rejected"}),
    0
)
```

---

## Vendor Measures

### Spend by Vendor (YTD)
```dax
Vendor Spend YTD =
CALCULATE([Spend YTD])
-- Apply in a visual with Vendor Name on axis
```

### Active Vendor Count
```dax
Active Vendors =
CALCULATE(COUNTROWS(Vendors), Vendors[Status] = "Approved")
```

### Unapproved Vendor Requests
```dax
Unapproved Vendor Requests =
CALCULATE(
    COUNTROWS('Purchase Requests'),
    'Purchase Requests'[Vendor Approved] = FALSE(),
    'Purchase Requests'[Status] NOT IN {"Rejected","Canceled","Draft"}
)
```

### Top Vendor by Spend
```dax
Vendor Rank =
RANKX(ALL(Vendors), [Vendor Spend YTD], , DESC, Dense)
```

---

## Spend Category Analysis

### Spend by Category
```dax
Category Spend =
CALCULATE(SUM('Purchase Requests'[Total Amount]),
          'Purchase Requests'[Status] IN {"Approved","PO Issued"})
-- Apply in a visual with Category on axis
```

### Category Share %
```dax
Category Share =
DIVIDE([Category Spend], CALCULATE([Approved Spend], ALL('Purchase Requests'[Category])), 0)
```

---

## Conditional Formatting

### Budget Status Color
```dax
Budget Status Color =
SWITCH(
    SELECTEDVALUE('Budget Codes'[Budget Status]),
    "Healthy",   "#27AE60",
    "At Risk",   "#F39C12",
    "Overspent", "#E74C3C",
    "#95A5A6"
)
```

### Approval Rate Color
```dax
Approval Rate Color =
SWITCH(
    TRUE(),
    [Approval Rate] >= 0.80, "#27AE60",
    [Approval Rate] >= 0.60, "#F39C12",
    "#E74C3C"
)
```
