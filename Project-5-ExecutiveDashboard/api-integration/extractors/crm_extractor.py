"""
Extractor: CRM-System Quickbase app.
Pulls all KPIs needed for the Commercial domain score.
"""

import logging
import requests
from datetime import datetime, timezone
from config import Config

log = logging.getLogger(__name__)

_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _query(table_id: str, select: list, where: str = "", top: int = 1000) -> list:
    body = {"from": table_id, "select": select, "options": {"top": top}}
    if where:
        body["where"] = where
    r = requests.post("https://api.quickbase.com/v1/records/query",
                      headers=_HEADERS, json=body, timeout=15)
    r.raise_for_status()
    return r.json().get("data", [])


def extract() -> dict:
    """
    Returns normalized CRM / Commercial KPIs.
    """
    log.info("Extracting CRM KPIs...")

    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")

    all_deals = _query(
        Config.QB_DEALS_TABLE,
        select=[3, 11, 12, 13, 14, 21, 24, 31, 32],
        top=2000,
    )

    open_deals   = [d for d in all_deals if d.get("11", {}).get("value") not in ("Closed Won", "Closed Lost")]
    won_deals    = [d for d in all_deals if d.get("11", {}).get("value") == "Closed Won"]
    lost_deals   = [d for d in all_deals if d.get("11", {}).get("value") == "Closed Lost"]
    closed_deals = won_deals + lost_deals

    def v(deal, fid): return deal.get(str(fid), {}).get("value")

    weighted_pipeline = sum(float(v(d, 14) or 0) for d in open_deals)

    won_mtd = sum(
        float(v(d, 12) or 0) for d in won_deals
        if (v(d, 16) or "")[:7] == current_month
    )

    win_rate = (len(won_deals) / len(closed_deals) * 100) if closed_deals else 0

    cycle_days = [float(v(d, 24) or 0) for d in won_deals if v(d, 24)]
    avg_cycle_days = sum(cycle_days) / len(cycle_days) if cycle_days else 0

    stalled = sum(1 for d in open_deals if v(d, 32) == "Stalled")
    at_risk  = sum(1 for d in open_deals if v(d, 32) in ("At Risk", "Stalled"))

    # Quota attainment — pull from reps table
    reps = _query(Config.QB_REPS_TABLE, select=[3, 10, 12, 13], where="{11.EX.'true'}")
    total_quota  = sum(float(r.get("10", {}).get("value") or 0) for r in reps)
    total_won_m  = sum(float(r.get("13", {}).get("value") or 0) for r in reps)
    quota_attainment = (total_won_m / total_quota * 100) if total_quota else 0

    pipeline_coverage = (weighted_pipeline / total_quota) if total_quota else 0

    log.info("CRM: pipeline R%.0f | win rate %.1f%% | quota %.1f%%",
             weighted_pipeline, win_rate, quota_attainment)

    return {
        "weighted_pipeline":   round(weighted_pipeline, 2),
        "won_revenue_mtd":     round(won_mtd, 2),
        "win_rate":            round(win_rate, 2),
        "avg_cycle_days":      round(avg_cycle_days, 1),
        "quota_attainment":    round(quota_attainment, 2),
        "stalled_deals":       stalled,
        "at_risk_deals":       at_risk,
        "pipeline_coverage":   round(pipeline_coverage, 2),
        "open_deal_count":     len(open_deals),
        "total_won_count":     len(won_deals),
        "total_lost_count":    len(lost_deals),
    }
