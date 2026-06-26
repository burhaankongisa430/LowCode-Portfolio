# Project 7: Digital Transformation Case Study

## Meridian Professional Services — 18-Month Digital Transformation Program

> *"This case study documents the end-to-end transformation of Meridian's operational landscape from a manual, email-driven organization to a fully automated, data-driven business. It serves as the flagship piece of the portfolio — demonstrating not just technical capability but the business value, process thinking, and stakeholder communication skills that separate a mid-level low-code developer from a transformation engineer."*

---

## Organization Context

**Meridian Professional Services (Pty) Ltd**
- Industry: Professional Services (consulting, managed services)
- Size: 280 employees, 4 departments, R120M annual revenue
- Location: Cape Town, South Africa (remote-first since 2022)
- Challenge: Rapid post-COVID growth had outpaced their manually-managed processes
- Trigger: Two enterprise clients threatened contract cancellation due to SLA misses and onboarding delays

**My Role:** Low-Code Solutions Engineer and Digital Transformation Lead
- Requirements gathering across 4 departments and 18 stakeholders
- End-to-end solution design, build, test, and deployment
- Stakeholder training, governance documentation, and change management support
- Ongoing monitoring via the Executive Dashboard (Project 5)

---

## Transformation Scope

Six platforms delivered across 18 months in two phases:

### Phase 1 — Operational Foundation (Months 1–9)
| Project | Platform | Primary Stakeholder |
|---------|---------|---------------------|
| 1. Service Desk Automation | Quickbase + Power Automate | COO / IT Manager |
| 2. CRM & Sales Pipeline | Quickbase + Power Automate | CRO / Sales Director |
| 3. Employee Onboarding | Quickbase + Power Automate + Azure AD | CHRO / HR Manager |

### Phase 2 — Enterprise Integration (Months 10–18)
| Project | Platform | Primary Stakeholder |
|---------|---------|---------------------|
| 4. Procurement Approval | Quickbase + Power Automate | CFO / Finance Manager |
| 5. Executive Dashboard | Power BI + Python ETL | CEO / All C-Suite |
| 6. API Integration Hub | Python + Quickbase | CTO / IT Director |

---

## Before-State Baseline (Month 0 Measurements)

| Domain | Metric | Baseline | Source |
|--------|--------|----------|--------|
| Service Desk | SLA met rate | 66% | Manual weekly report |
| Service Desk | Avg resolution time | 48 hours | Email timestamp analysis |
| Service Desk | Agent hours on admin/routing | 14h/agent/week | Time-in-motion study |
| Service Desk | P1 breaches per month | 8–12 | Incident log |
| Sales | Win rate | 22% | CRM spreadsheet |
| Sales | Avg sales cycle | 8.3 days | Deal spreadsheet |
| Sales | Time lost to manual CRM updates | 7h/rep/week | Survey |
| Sales | Forecast accuracy | ±40% | Finance vs actuals |
| HR/Onboarding | Time-to-productivity | 47 days | Manager survey |
| HR/Onboarding | Onboarding completion rate | 58% | HR tracking sheet |
| HR/Onboarding | Day 1 system access achieved | 31% | IT records |
| HR/Onboarding | HR admin hours per new hire | 18h/hire | Time study |
| Procurement | Approval cycle time | 8.3 days | Email thread analysis |
| Procurement | Manual PO creation time | 3h/PO | Finance team survey |
| Procurement | Budget overspend incidents | 6/year | Finance records |
| Procurement | Lost invoices / payment delays | 14/year | AP records |
| Integration | Data entry duplication | 4.2 systems/record | IT audit |
| Integration | Integration failures (silent) | ~340/month est. | IT audit |
| Integration | Time spent on cross-system updates | 22h/week (all teams) | Survey |

---

## After-State Results (Month 18 Measurements)

| Domain | Metric | Before | After | Change |
|--------|--------|--------|-------|--------|
| Service Desk | SLA met rate | 66% | 94% | **+28pp** |
| Service Desk | Avg resolution time | 48h | 18h | **−63%** |
| Service Desk | Admin/routing hours | 14h/week | 2h/week | **−86%** |
| Service Desk | P1 breaches/month | 10 avg | 1.2 avg | **−88%** |
| Sales | Win rate | 22% | 31% | **+9pp** |
| Sales | Avg sales cycle | 8.3 days | 6.2 days | **−25%** |
| Sales | Manual CRM update time | 7h/rep/week | 0.5h | **−93%** |
| Sales | Forecast accuracy | ±40% | ±12% | **+70%** |
| HR/Onboarding | Time-to-productivity | 47 days | 28 days | **−40%** |
| HR/Onboarding | Onboarding completion rate | 58% | 97% | **+39pp** |
| HR/Onboarding | Day 1 system access | 31% | 94% | **+63pp** |
| HR/Onboarding | HR admin hours/hire | 18h | 3h | **−83%** |
| Procurement | Approval cycle | 8.3 days | 1.4 days | **−83%** |
| Procurement | PO creation time | 3h/PO | 0 (automated) | **−100%** |
| Procurement | Budget overspend incidents | 6/year | 0 | **−100%** |
| Procurement | Lost invoices | 14/year | 1 | **−93%** |
| Integration | Cross-system update time | 22h/week | 1.5h/week | **−93%** |
| Integration | Event success rate | ~60% (est.) | 94% | **+34pp** |

---

## Financial ROI Summary

| Benefit Category | Annual Value (ZAR) |
|-----------------|-------------------|
| Labor Efficiency (hours saved) | R 2,184,000 |
| Revenue Enablement (sales + onboarding) | R 3,960,000 |
| Risk Reduction (SLA penalties + compliance) | R 840,000 |
| Cost Avoidance (procurement + integration) | R 1,128,000 |
| **Total Annual Benefits** | **R 8,112,000** |
| Total Investment (18 months) | R 1,950,000 |
| **Net First-Year Benefit** | **R 6,162,000** |
| **ROI** | **316%** |
| **Payback Period** | **2.9 months** |
| **3-Year NPV (10% discount)** | **R 18,240,000** |

> *Full ROI methodology and calculations are in `docs/roi-methodology.md` and `api-integration/roi_calculator.py`*

---

## Project Structure

```
LowCode-Portfolio/DigitalTransformationCaseStudy/
├── README.md                            # This file — executive summary
├── docs/
│   ├── transformation-scope.md          # Before/after process analysis + swimlanes
│   └── roi-methodology.md               # How every number was calculated
├── quickbase/
│   ├── formulas.md                      # Transformation tracking formulas
│   └── automations.md                   # Milestone and reporting automations
├── power-platform/
│   ├── flows/
│   │   ├── 01-monthly-roi-report.json
│   │   ├── 02-milestone-completion.json
│   │   ├── 03-stakeholder-progress-update.json
│   │   └── 04-benefit-realization-alert.json
│   ├── power-apps/
│   │   └── canvas-app-formulas.md       # Transformation Tracker portal
│   └── power-bi/
│       └── dax-measures.md              # Impact analytics dashboard
└── api-integration/
    ├── requirements.txt
    ├── config.py
    ├── baseline_collector.py            # Before-state metric capture tool
    ├── roi_calculator.py                # Financial ROI computation engine
    ├── impact_analyzer.py               # Before/after comparison engine
    ├── report_generator.py              # Executive HTML transformation report
    └── webhook_handler.py               # Flask server + API endpoints
```

---

## What Makes This the Right Flagship Closer

Projects 1–6 prove technical depth. Project 7 proves something harder to teach: the ability to frame technical work as business value, measure it rigorously, and communicate it to people who do not care about code.

| Area | What's unique here |
|------|-------------------|
| **Business problem framing** | `docs/transformation-scope.md` documents full AS-IS → TO-BE process analysis for all 4 domains, including the discovery methodology, friction audit approach, stakeholder map, and change management cadence — the work that happens before any tool is selected |
| **ROI methodology** | `docs/roi-methodology.md` sources every financial figure, applies a 15% uncertainty discount, and had each number verified by the CFO. Five benefit categories with individual confidence ratings. This answers the interview question: "how do you measure the impact of your work?" |
| **Financial engine** | `roi_calculator.py` computes NPV, payback period, benefit realization rate, and a 3-scenario sensitivity analysis (pessimistic / base / optimistic) from a single `compute()` call. Uses named tuples so every field is explicitly typed |
| **Discovery data as code** | `baseline_collector.py` holds the `MERIDIAN_BASELINES` seed list — a structured record of all before-state measurements. `seed_meridian_baselines()` loads the entire discovery into QB in one command; `record_after_metric()` closes the loop when measurements are taken post-deployment |
| **Executive report quality** | `report_generator.py` produces a pixel-perfect, mobile-responsive HTML email with headline KPIs, per-initiative ROI table with RAG color coding, benefit category breakdown with confidence bars, sensitivity analysis cards, and top process wins — zero external library dependencies |
| **Ties all 6 projects together** | The `config.py` `INITIATIVES` dict references all six prior platforms by name, investment, OPEX, and projected benefit — making this the single file in the portfolio where the entire program is visible end-to-end |
| **Adoption ramp modeling** | `ADOPTION_RAMP` applies an 18-point benefit accrual schedule that accounts for the lag between go-live and full adoption, producing more honest projected vs. actual comparisons than a straight-line assumption |

---

## Key Lessons Learned

### What drove success

1. **Starting with measurement, not tools.** Running a time-in-motion study in Week 1 gave us hard numbers, not opinions. Every stakeholder approved the project because they saw their own pain quantified.

2. **Phasing by dependency.** Phase 1 established the data model and the culture of "logging everything." Phase 2 then had clean, structured data to integrate against. Building the API Hub (Project 6) before the data was clean would have integrated chaos.

3. **Approver buy-in through early wins.** Project 1 (Service Desk) delivered visible results within 6 weeks. The COO became our internal champion. Every subsequent project had executive air cover because of that early win.

4. **Role-based access from day one.** Every Quickbase app was built with role-based permissions from the first day. Retroactively adding security creates angst and rework.

5. **The Executive Dashboard created accountability.** Once leadership could see their domain score in real time, they stopped asking for status updates and started driving their own teams to improve the metrics.

### What would I do differently

1. **Document the current state more rigorously before any build.** We discovered 3 shadow Excel systems mid-project that weren't in scope.

2. **Budget 20% extra for change management.** The technology was ready before the people were. Adoption training was underscoped.

3. **Build the Integration Hub (Project 6) in Phase 1.** We retrofitted integrations that should have been designed from the start.
