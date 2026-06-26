"""
KPI Calculator — the intelligence core of the Executive Dashboard.

Takes the raw domain data dicts from all 4 extractors and produces:
  1. A domain score for each area (0–100)
  2. A weighted composite Organizational Health Score (0–100)
  3. A list of threshold breach alerts with severity
  4. The unified KPI payload written to Quickbase and Dataverse

Domain scoring is intentionally transparent and tunable via config.py.
Every scoring decision is a documented formula, not a black box.
"""

import logging
from config import Config

log = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Helper: scale a value to a 0-100 score                            #
# ------------------------------------------------------------------ #

def _score_rate(actual: float, target: float, floor: float = 0,
                higher_is_better: bool = True) -> float:
    """
    Convert a rate-type KPI to a 0–100 score.
    higher_is_better=True: score = (actual / target) * 100, capped at 100
    higher_is_better=False: score = (target / actual) * 100 (e.g., breach counts)
    """
    if higher_is_better:
        if target <= 0:
            return 100.0
        return min(100.0, max(0.0, (actual / target) * 100))
    else:
        if actual <= 0:
            return 100.0
        return min(100.0, max(0.0, (target / actual) * 100))


def _score_inverse(actual: float, bad_value: float) -> float:
    """Score where 0 is perfect and bad_value means score = 0."""
    if actual <= 0:
        return 100.0
    return max(0.0, 100.0 - (actual / bad_value) * 100)


# ------------------------------------------------------------------ #
#  Domain Scorers                                                      #
# ------------------------------------------------------------------ #

def score_operational(ops: dict) -> float:
    """
    Operational domain score (Service Desk).

    Components:
      - SLA Met Rate       (weight 0.40): target 95%, min 50%
      - Active Breaches    (weight 0.30): 0 = 100 score, 10+ = 0
      - Avg Resolution Hrs (weight 0.20): target ≤ 4h (P1), overall target ≤ 24h
      - P1 Breach Count    (weight 0.10): 0 = 100, 1+ drops fast
    """
    sla_score       = _score_rate(ops.get("sla_met_rate", 100), 95) * 0.40
    breach_score    = _score_inverse(ops.get("active_breaches", 0), 10) * 0.30
    resolution_score= _score_rate(24, ops.get("avg_resolution_hours", 0), higher_is_better=False) * 0.20
    p1_score        = _score_inverse(ops.get("p1_breach_count", 0), 3) * 0.10

    score = sla_score + breach_score + resolution_score + p1_score
    log.debug("Operational score: %.1f (sla=%.1f, breach=%.1f, res=%.1f, p1=%.1f)",
              score, sla_score, breach_score, resolution_score, p1_score)
    return round(score, 2)


def score_commercial(crm: dict) -> float:
    """
    Commercial domain score (CRM / Sales).

    Components:
      - Win Rate         (weight 0.30): target 40%
      - Quota Attainment (weight 0.35): target 100%
      - Stalled Deals    (weight 0.20): 0 = 100, 10+ = 0
      - Pipeline Coverage(weight 0.15): target 3× quota
    """
    win_score      = _score_rate(crm.get("win_rate", 0), 40) * 0.30
    quota_score    = _score_rate(crm.get("quota_attainment", 0), 100) * 0.35
    stalled_score  = _score_inverse(crm.get("stalled_deals", 0), 10) * 0.20
    coverage_score = _score_rate(crm.get("pipeline_coverage", 0), 3) * 0.15

    score = win_score + quota_score + stalled_score + coverage_score
    log.debug("Commercial score: %.1f", score)
    return round(score, 2)


def score_people(hr: dict) -> float:
    """
    People domain score (HR / Onboarding).

    Components:
      - On Track Rate    (weight 0.40): target 95%
      - Day 1 Readiness  (weight 0.35): target 100%
      - Avg Completion   (weight 0.15): target ≤ 30 days
      - Overdue Tasks    (weight 0.10): 0 = 100, 20+ = 0
    """
    on_track_score  = _score_rate(hr.get("on_track_rate", 100), 95) * 0.40
    day1_score      = _score_rate(hr.get("day1_readiness_rate", 100), 100) * 0.35
    completion_score= _score_rate(30, hr.get("avg_completion_days", 30), higher_is_better=False) * 0.15
    overdue_score   = _score_inverse(hr.get("overdue_tasks_total", 0), 20) * 0.10

    score = on_track_score + day1_score + completion_score + overdue_score
    log.debug("People score: %.1f", score)
    return round(score, 2)


def score_finance(fin: dict) -> float:
    """
    Finance domain score (Procurement).

    Components:
      - Budget Utilization  (weight 0.30): target ≤ 85%, 100%+ = bad
      - Approval Cycle Days (weight 0.30): target ≤ 2 days
      - Pending Approvals   (weight 0.25): 0 = 100, 25+ = 0
      - Over-Budget Depts   (weight 0.15): 0 = 100, 3+ = 0
    """
    util = fin.get("avg_budget_utilization", 0)
    budget_score   = _score_rate(85, util, higher_is_better=False) * 0.30 if util > 0 else 100 * 0.30
    cycle_score    = _score_rate(2, fin.get("avg_approval_cycle_days", 0), higher_is_better=False) * 0.30
    pending_score  = _score_inverse(fin.get("pending_approvals", 0), 25) * 0.25
    overspend_score= _score_inverse(fin.get("over_budget_depts", 0), 3) * 0.15

    score = budget_score + cycle_score + pending_score + overspend_score
    log.debug("Finance score: %.1f", score)
    return round(score, 2)


# ------------------------------------------------------------------ #
#  Health Score Labeling                                              #
# ------------------------------------------------------------------ #

def _health_label(score: float) -> tuple[str, str]:
    """Returns (status_label, hex_color)."""
    t = Config.HEALTH_THRESHOLDS
    if score >= t["excellent"]:
        return "Excellent",       "#27AE60"
    if score >= t["good"]:
        return "Good",            "#2ECC71"
    if score >= t["needs_attention"]:
        return "Needs Attention", "#F39C12"
    if score >= t["at_risk"]:
        return "At Risk",         "#E67E22"
    return "Critical",            "#E74C3C"


# ------------------------------------------------------------------ #
#  Alert Generation                                                    #
# ------------------------------------------------------------------ #

def _check_alerts(kpis: dict) -> list[dict]:
    """
    Compare KPI values against thresholds from config.
    Returns a list of alert dicts, each with domain, kpiName,
    currentValue, thresholdValue, severity, message.
    """
    alerts = []
    thresholds = Config.KPI_THRESHOLDS

    def alert(domain, name, current, warn_t, crit_t, higher_is_better=False):
        """higher_is_better=False means we alert when value is TOO HIGH."""
        if higher_is_better:
            if current < crit_t:
                sev = "Critical"
            elif current < warn_t:
                sev = "Warning"
            else:
                return
            msg = f"{name} is {current:.1f}, below {warn_t if sev == 'Warning' else crit_t} threshold."
        else:
            if current >= crit_t:
                sev = "Critical"
            elif current >= warn_t:
                sev = "Warning"
            else:
                return
            msg = f"{name} is {current:.1f}, exceeding {warn_t if sev == 'Warning' else crit_t} threshold."

        alerts.append({
            "domain":         domain,
            "kpiName":        name,
            "currentValue":   round(current, 2),
            "thresholdValue": warn_t if sev == "Warning" else crit_t,
            "severity":       sev,
            "message":        msg,
        })

    # Higher is better (alert if below threshold)
    alert("Overall",     "Health Score",           kpis["health_score"],       *thresholds["health_score"],       True)
    alert("Operational", "SLA Met Rate (%)",        kpis["sla_met_rate"],       *thresholds["sla_met_rate"],       True)
    alert("Commercial",  "Win Rate (%)",             kpis["win_rate"],           *thresholds["win_rate"],           True)
    alert("Commercial",  "Quota Attainment (%)",     kpis["quota_attainment"],   *thresholds["quota_attainment"],   True)
    alert("People",      "Onboarding On Track (%)",  kpis["onboarding_on_track_rate"], *thresholds["onboarding_on_track_rate"], True)

    # Lower is better (alert if above threshold)
    alert("Operational", "Active Breaches",          kpis["active_breaches"],    *thresholds["active_breaches"],    False)
    alert("Finance",     "Avg Budget Utilization (%)",kpis["avg_budget_util"],   *thresholds["avg_budget_util"],    False)
    alert("Finance",     "Pending Approvals",         kpis["pending_approvals"],  *thresholds["pending_approvals"],  False)

    return alerts


# ------------------------------------------------------------------ #
#  Main compute function                                               #
# ------------------------------------------------------------------ #

def compute(ops: dict, crm: dict, hr: dict, fin: dict,
            domains_available: int = 4, etl_duration: float = 0) -> dict:
    """
    Compute all domain scores, the composite health score, and alerts.

    Returns the complete KPI payload ready for writing to QB and Dataverse.
    """
    w = Config.DOMAIN_WEIGHTS

    op_score  = score_operational(ops) if ops else 0
    com_score = score_commercial(crm)  if crm else 0
    ppl_score = score_people(hr)       if hr  else 0
    fin_score = score_finance(fin)     if fin else 0

    health = round(
        op_score  * w["operational"] +
        com_score * w["commercial"] +
        ppl_score * w["people"] +
        fin_score * w["finance"],
        2
    )

    status, color = _health_label(health)

    kpis = {
        # Scores
        "health_score":           health,
        "health_status":          status,
        "health_color":           color,
        "operational_score":      op_score,
        "commercial_score":       com_score,
        "people_score":           ppl_score,
        "finance_score":          fin_score,

        # Operational KPIs
        "sla_met_rate":           ops.get("sla_met_rate", 0) if ops else 0,
        "active_breaches":        ops.get("active_breaches", 0) if ops else 0,
        "avg_resolution_hours":   ops.get("avg_resolution_hours", 0) if ops else 0,
        "open_tickets":           ops.get("open_tickets", 0) if ops else 0,
        "p1_breach_count":        ops.get("p1_breach_count", 0) if ops else 0,

        # Commercial KPIs
        "weighted_pipeline":      crm.get("weighted_pipeline", 0) if crm else 0,
        "won_revenue_mtd":        crm.get("won_revenue_mtd", 0) if crm else 0,
        "win_rate":               crm.get("win_rate", 0) if crm else 0,
        "quota_attainment":       crm.get("quota_attainment", 0) if crm else 0,
        "stalled_deals":          crm.get("stalled_deals", 0) if crm else 0,

        # People KPIs
        "active_onboarding":      hr.get("active_onboarding", 0) if hr else 0,
        "onboarding_on_track_rate":hr.get("on_track_rate", 0) if hr else 0,
        "avg_completion_days":    hr.get("avg_completion_days", 0) if hr else 0,
        "day1_readiness_rate":    hr.get("day1_readiness_rate", 0) if hr else 0,
        "overdue_tasks_total":    hr.get("overdue_tasks_total", 0) if hr else 0,

        # Finance KPIs
        "committed_spend_mtd":    fin.get("committed_spend_mtd", 0) if fin else 0,
        "avg_budget_util":        fin.get("avg_budget_utilization", 0) if fin else 0,
        "pending_approvals":      fin.get("pending_approvals", 0) if fin else 0,
        "approval_cycle_days":    fin.get("avg_approval_cycle_days", 0) if fin else 0,
        "over_budget_depts":      fin.get("over_budget_depts", 0) if fin else 0,

        # Meta
        "domains_available":      domains_available,
        "etl_duration_seconds":   etl_duration,
    }

    kpis["alerts"] = _check_alerts(kpis)

    log.info(
        "Health: %.1f (%s) | Ops: %.1f | Sales: %.1f | People: %.1f | Finance: %.1f | Alerts: %d",
        health, status, op_score, com_score, ppl_score, fin_score, len(kpis["alerts"])
    )
    return kpis
