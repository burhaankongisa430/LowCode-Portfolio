"""
ROI Calculator — the financial intelligence core of the transformation program.

Computes:
  1. Per-initiative ROI, payback period, and NPV
  2. Program-level aggregated financials
  3. Benefit realization rate (actual vs projected)
  4. 3-year NPV at a configurable discount rate
  5. Monthly benefit accrual schedule
  6. Sensitivity analysis (best/base/worst case)

Designed to be called:
  - Monthly by the APScheduler (automatic report)
  - On-demand via the Flask API
  - From the Power Automate monthly report flow
"""

import logging
from datetime import datetime, timezone
from typing import NamedTuple
from config import Config

log = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Data structures                                                    #
# ------------------------------------------------------------------ #

class BenefitCategory(NamedTuple):
    name:         str
    annual_value: float
    description:  str
    confidence:   float  # 0.0–1.0 — how certain is this figure?


class InitiativeROI(NamedTuple):
    initiative_id:          str
    name:                   str
    domain:                 str
    investment:             float
    annual_opex:            float
    projected_annual:       float
    actual_annual:          float
    actual_ytd:             float
    projected_ytd:          float
    roi_pct:                float
    payback_months:         float
    npv_3yr:                float
    realization_pct:        float
    realization_status:     str


class ProgramROI(NamedTuple):
    total_investment:        float
    total_annual_opex:       float
    total_projected_annual:  float
    total_actual_annual:     float
    total_actual_ytd:        float
    total_projected_ytd:     float
    program_roi_pct:       float
    program_payback_months:float
    program_npv_3yr:       float
    benefit_realization_pct: float
    realization_status:      str
    initiative_rois:         list[InitiativeROI]
    benefit_categories:      list[BenefitCategory]
    monthly_schedule:        list[dict]
    sensitivity:             dict
    snapshot_time:           str


# ------------------------------------------------------------------ #
#  Core calculations                                                  #
# ------------------------------------------------------------------ #

def _npv(annual_net_benefit: float, years: int = 3,
         discount_rate: float = None) -> float:
    """Net Present Value over `years` years."""
    rate = discount_rate or Config.DISCOUNT_RATE
    total = 0.0
    for yr in range(1, years + 1):
        total += annual_net_benefit / ((1 + rate) ** yr)
    return total


def _payback_months(investment: float, monthly_net_benefit: float) -> float:
    """Months to recover the investment. Returns inf if benefit is zero."""
    if monthly_net_benefit <= 0:
        return float("inf")
    return investment / monthly_net_benefit


def _realization_status(pct: float) -> str:
    if pct >= Config.REALISATION_EXCELLENT:
        return "Exceeding"
    if pct >= Config.REALISATION_ON_TRACK:
        return "On Track"
    if pct >= Config.REALISATION_AT_RISK:
        return "At Risk"
    return "Underperforming"


def _months_elapsed(program_start: str) -> int:
    """How many calendar months since the program started."""
    start = datetime.strptime(program_start, "%Y-%m-%d")
    now   = datetime.now(timezone.utc).replace(tzinfo=None)
    return max(1, (now.year - start.year) * 12 + (now.month - start.month))


# ------------------------------------------------------------------ #
#  Benefit category definitions                                       #
# These mirror the methodology in docs/roi-methodology.md            #
# ------------------------------------------------------------------ #

BENEFIT_CATEGORIES = [
    BenefitCategory(
        name="Labor Efficiency",
        annual_value=2_184_000,
        description="Hours saved across all teams — routing, admin, CRM updates, PO creation, cross-system updates",
        confidence=0.90,
    ),
    BenefitCategory(
        name="Revenue Enablement",
        annual_value=3_960_000,
        description="Win rate improvement (9pp) + faster time-to-productivity (19 days/hire)",
        confidence=0.75,
    ),
    BenefitCategory(
        name="Risk Reduction",
        annual_value=840_000,
        description="SLA penalty avoidance + client retention + compliance incidents avoided",
        confidence=0.65,
    ),
    BenefitCategory(
        name="Cost Avoidance",
        annual_value=1_128_000,
        description="Avoided headcount + avoided iPaaS license + avoided consultant + reduced attrition",
        confidence=0.80,
    ),
]

TOTAL_ANNUAL_BENEFIT = sum(c.annual_value for c in BENEFIT_CATEGORIES)
WEIGHTED_CONFIDENCE  = sum(c.annual_value * c.confidence for c in BENEFIT_CATEGORIES) / TOTAL_ANNUAL_BENEFIT


# ------------------------------------------------------------------ #
#  Monthly adoption ramp                                              #
# Benefits accrue gradually as adoption increases                    #
# ------------------------------------------------------------------ #

ADOPTION_RAMP = [
    # (month, cumulative_pct_of_full_annual_benefit)
    (1,  0.00), (2,  0.10), (3,  0.25), (4,  0.40), (5,  0.55),
    (6,  0.65), (7,  0.72), (8,  0.78), (9,  0.83), (10, 0.86),
    (11, 0.89), (12, 0.92), (13, 0.94), (14, 0.96), (15, 0.97),
    (16, 0.98), (17, 0.99), (18, 1.00),
]


def _projected_ytd(initiative_id: str, months_in: int) -> float:
    """Projected cumulative benefit for an initiative at `months_in` months."""
    annual = Config.INITIATIVES[initiative_id]["projected_annual_benefit"]
    # Each initiative starts at a different month; simplified: all start month 1
    monthly = annual / 12
    cumulative = 0.0
    for month, ramp_pct in ADOPTION_RAMP:
        if month > months_in:
            break
        prev_pct = ADOPTION_RAMP[month - 2][1] if month > 1 else 0.0
        month_increment = (ramp_pct - prev_pct) * annual
        cumulative += month_increment
    return round(cumulative, 2)


# ------------------------------------------------------------------ #
#  Main calculator                                                    #
# ------------------------------------------------------------------ #

def compute(actual_benefits_by_initiative: dict = None,
            program_start: str = "2024-01-01") -> ProgramROI:
    """
    Compute the full program ROI.

    actual_benefits_by_initiative: {initiative_id: actual_annual_benefit}
    If not provided, uses the projected figures (for forecasting mode).
    """
    now = datetime.now(timezone.utc)
    months_in = _months_elapsed(program_start)

    if actual_benefits_by_initiative is None:
        # Use projected as actuals for demonstration/forecasting
        actual_benefits_by_initiative = {
            iid: cfg["projected_annual_benefit"]
            for iid, cfg in Config.INITIATIVES.items()
        }

    initiative_rois = []
    for iid, cfg in Config.INITIATIVES.items():
        actual_annual  = actual_benefits_by_initiative.get(iid, 0)
        projected_ytd  = _projected_ytd(iid, months_in)
        actual_ytd     = round(actual_annual / 12 * months_in, 2)  # linear simplification
        net_monthly    = (actual_annual - cfg["annual_opex"]) / 12
        payback        = _payback_months(cfg["investment"], net_monthly)
        npv            = _npv(actual_annual - cfg["annual_opex"])
        roi_pct        = round((actual_annual - cfg["investment"] - cfg["annual_opex"]) /
                               cfg["investment"] * 100, 1) if cfg["investment"] else 0
        realization_pct = round(actual_ytd / projected_ytd * 100, 1) if projected_ytd else 100

        initiative_rois.append(InitiativeROI(
            initiative_id      = iid,
            name               = cfg["name"],
            domain             = cfg["domain"],
            investment         = cfg["investment"],
            annual_opex        = cfg["annual_opex"],
            projected_annual   = cfg["projected_annual_benefit"],
            actual_annual      = actual_annual,
            actual_ytd         = actual_ytd,
            projected_ytd      = projected_ytd,
            roi_pct            = roi_pct,
            payback_months     = round(payback, 1),
            npv_3yr            = round(npv, 0),
            realization_pct    = realization_pct,
            realization_status = _realization_status(realization_pct),
        ))

    total_actual    = sum(i.actual_annual for i in initiative_rois)
    total_projected = sum(i.projected_annual for i in initiative_rois)
    total_ytd       = sum(i.actual_ytd for i in initiative_rois)
    proj_ytd_total  = sum(i.projected_ytd for i in initiative_rois)
    total_opex      = Config.TOTAL_ANNUAL_OPEX
    total_invest    = Config.TOTAL_INVESTMENT

    prog_roi         = round((total_actual - total_invest - total_opex) / total_invest * 100, 1)
    prog_net_monthly = (total_actual - total_opex) / 12
    prog_payback     = _payback_months(total_invest, prog_net_monthly)
    prog_npv         = _npv(total_actual - total_opex)
    prog_realization = round(total_ytd / proj_ytd_total * 100, 1) if proj_ytd_total else 100

    monthly_schedule = []
    cumulative_invest = total_invest
    cumulative_benefit = 0.0
    for month, ramp_pct in ADOPTION_RAMP:
        prev = ADOPTION_RAMP[month - 2][1] if month > 1 else 0.0
        month_benefit   = (ramp_pct - prev) * total_actual
        cumulative_benefit += month_benefit
        net_cumulative  = cumulative_benefit - cumulative_invest
        monthly_schedule.append({
            "month":             month,
            "adoptionPct":       round(ramp_pct * 100, 0),
            "monthlyBenefit":    round(month_benefit, 0),
            "cumulativeBenefit": round(cumulative_benefit, 0),
            "cumulativeInvest":  round(cumulative_invest, 0),
            "netCumulative":     round(net_cumulative, 0),
            "isProfitable":      net_cumulative > 0,
        })
        cumulative_invest = 0  # Investment is front-loaded month 0

    sensitivity = {
        "pessimistic": {
            "label":       "Pessimistic (−20% on benefits)",
            "annual":      round(total_actual * 0.80, 0),
            "roi_pct":     round((total_actual * 0.80 - total_invest - total_opex) / total_invest * 100, 1),
            "payback":     round(_payback_months(total_invest, (total_actual * 0.80 - total_opex) / 12), 1),
            "npv_3yr":     round(_npv(total_actual * 0.80 - total_opex), 0),
        },
        "base": {
            "label":       "Base Case",
            "annual":      round(total_actual, 0),
            "roi_pct":     prog_roi,
            "payback":     round(prog_payback, 1),
            "npv_3yr":     round(prog_npv, 0),
        },
        "optimistic": {
            "label":       "Optimistic (+15% on benefits)",
            "annual":      round(total_actual * 1.15, 0),
            "roi_pct":     round((total_actual * 1.15 - total_invest - total_opex) / total_invest * 100, 1),
            "payback":     round(_payback_months(total_invest, (total_actual * 1.15 - total_opex) / 12), 1),
            "npv_3yr":     round(_npv(total_actual * 1.15 - total_opex), 0),
        },
    }

    log.info("ROI computed: %.1f%% | Payback: %.1f months | NPV: R%.0f",
             prog_roi, prog_payback, prog_npv)

    return ProgramROI(
        total_investment         = total_invest,
        total_annual_opex        = total_opex,
        total_projected_annual   = total_projected,
        total_actual_annual      = total_actual,
        total_actual_ytd         = round(total_ytd, 0),
        total_projected_ytd      = round(proj_ytd_total, 0),
        program_roi_pct        = prog_roi,
        program_payback_months = round(prog_payback, 1),
        program_npv_3yr        = round(prog_npv, 0),
        benefit_realization_pct  = prog_realization,
        realization_status       = _realization_status(prog_realization),
        initiative_rois          = initiative_rois,
        benefit_categories       = list(BENEFIT_CATEGORIES),
        monthly_schedule         = monthly_schedule,
        sensitivity              = sensitivity,
        snapshot_time            = now.isoformat(),
    )
