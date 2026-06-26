"""
Rule-based lead scoring engine.
Computes a 0–100 score from 5 weighted signals and returns a grade.

Designed to be swap-replaceable with an ML model:
- Same input schema
- Same output schema: {"score": int, "grade": str, "breakdown": dict}
- Same HTTP endpoint in webhook_handler.py

Weights are tunable in config.py without touching this file.
"""

from config import Config


C_SUITE_TITLES  = {"ceo", "coo", "cto", "cfo", "ciso", "cmo", "chief"}
VP_TITLES       = {"vp", "vice president", "vice-president"}
DIRECTOR_TITLES = {"director", "head of", "head,"}
MANAGER_TITLES  = {"manager", "lead", "principal", "senior manager"}


def _classify_job_title(job_title: str) -> str:
    if not job_title:
        return "Other"
    lower = job_title.lower()
    if any(t in lower for t in C_SUITE_TITLES):
        return "C-Suite"
    if any(t in lower for t in VP_TITLES):
        return "VP"
    if any(t in lower for t in DIRECTOR_TITLES):
        return "Director"
    if any(t in lower for t in MANAGER_TITLES):
        return "Manager"
    return "Other"


def _score_lead_source(lead_source: str) -> int:
    weights = Config.LEAD_SCORE_WEIGHTS["lead_source"]
    return weights.get(lead_source, 3)


def _score_company_size(company_size: str) -> int:
    weights = Config.LEAD_SCORE_WEIGHTS["company_size"]
    return weights.get(company_size, 4)


def _score_industry(industry: str) -> int:
    weights = Config.LEAD_SCORE_WEIGHTS["industry"]
    return weights.get(industry, 5)


def _score_job_title(job_title: str) -> int:
    tier = _classify_job_title(job_title)
    return Config.LEAD_SCORE_WEIGHTS["job_title_tier"].get(tier, 4)


def _score_deal_value(deal_value: float) -> int:
    cfg = Config.LEAD_SCORE_WEIGHTS["deal_value"]
    if deal_value >= cfg["threshold_high"]:
        return cfg["score_high"]
    if deal_value >= cfg["threshold_mid"]:
        return cfg["score_mid"]
    return cfg["score_low"]


def _email_domain_bonus(email: str) -> int:
    """
    Small bonus for corporate email domains vs free providers.
    Free providers indicate a lower-intent / consumer lead.
    """
    free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}
    domain = email.split("@")[-1].lower() if "@" in email else ""
    return 0 if domain in free_domains else 5


def score_lead(
    lead_source: str,
    job_title: str,
    company_size: str,
    industry: str,
    deal_value: float,
    email: str,
) -> dict:
    """
    Score a lead and return a dict with total score, letter grade, and per-signal breakdown.

    Returns:
        {
            "score": 68,
            "grade": "B – Warm",
            "breakdown": {
                "lead_source": 18,
                "company_size": 12,
                "industry": 14,
                "job_title": 16,
                "deal_value": 8,
                "email_domain": 0,
            }
        }
    """
    breakdown = {
        "lead_source":  _score_lead_source(lead_source),
        "company_size": _score_company_size(company_size),
        "industry":     _score_industry(industry),
        "job_title":    _score_job_title(job_title),
        "deal_value":   _score_deal_value(deal_value or 0),
        "email_domain": _email_domain_bonus(email or ""),
    }

    raw_total = sum(breakdown.values())

    # Max possible is 20+20+15+20+15+5 = 95 — normalize to 0–100
    max_possible = 95
    score = round(min(100, (raw_total / max_possible) * 100))

    if score >= 75:
        grade = "A – Hot"
    elif score >= 50:
        grade = "B – Warm"
    elif score >= 25:
        grade = "C – Cool"
    else:
        grade = "D – Cold"

    return {"score": score, "grade": grade, "breakdown": breakdown}
