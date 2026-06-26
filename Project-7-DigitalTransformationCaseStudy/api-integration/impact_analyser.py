"""
Impact Analyzer — compares before and after baseline metrics.

Reads the Process Baselines table from Quickbase (where after-state
measurements have been logged by the team) and produces a structured
comparison report: improvement %, target met/missed, top wins, gaps.
"""

import logging
import requests
from config import Config

log = logging.getLogger(__name__)

_HEADERS = {
    "QB-Realm-Hostname": Config.QB_REALM,
    "Authorization":     f"QB-USER-TOKEN {Config.QB_TOKEN}",
    "Content-Type":      "application/json",
}


def _fetch_baselines(initiative_record_id: int = None) -> list[dict]:
    where = f"{{6.EX.'{initiative_record_id}'}}" if initiative_record_id else ""
    r = requests.post("https://api.quickbase.com/v1/records/query",
                      headers=_HEADERS,
                      json={
                          "from": Config.QB_BASELINES_TABLE,
                          "select": [3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18],
                          "where": where,
                          "options": {"top": 500},
                      }, timeout=10)
    r.raise_for_status()
    rows = r.json().get("data", [])

    def v(row, fid): return row.get(str(fid), {}).get("value")
    return [
        {
            "recordId":       v(row, 3),
            "initiative":     v(row, 6),
            "metric":         v(row, 7),
            "domain":         v(row, 8),
            "before":         float(v(row, 9) or 0),
            "unit":           v(row, 10),
            "direction":      v(row, 11),
            "after":          float(v(row, 12) or 0) if v(row, 12) is not None else None,
            "target":         float(v(row, 13) or 0),
            "improvementPct": float(v(row, 14) or 0) if v(row, 14) is not None else None,
            "targetMet":      v(row, 15),
            "method":         v(row, 17),
            "source":         v(row, 18),
        }
        for row in rows
    ]


def _compute_improvement(before: float, after: float, direction: str) -> float:
    """Calculate improvement % — positive always means 'better'."""
    if before == 0:
        return 0.0
    if direction == "Higher is Better":
        return (after - before) / abs(before) * 100
    return (before - after) / abs(before) * 100


def analyze(initiative_record_id: int = None) -> dict:
    """
    Produce a structured impact analysis report.

    Returns a dict with:
      - summary: totals and averages
      - by_domain: metrics grouped by domain with averages
      - top_wins: top 5 improvements by % gain
      - gaps: metrics where target was NOT met
      - measurement_coverage: % of metrics with after-state recorded
    """
    metrics = _fetch_baselines(initiative_record_id)

    measured     = [m for m in metrics if m["after"] is not None]
    unmeasured   = [m for m in metrics if m["after"] is None]
    targets_met  = [m for m in measured if m["targetMet"]]
    targets_miss = [m for m in measured if not m["targetMet"]]

    # Compute improvement for any metrics where it wasn't pre-computed
    for m in measured:
        if m["improvementPct"] is None and m["before"] != 0:
            m["improvementPct"] = _compute_improvement(m["before"], m["after"], m["direction"])

    coverage = len(measured) / len(metrics) * 100 if metrics else 0
    target_rate = len(targets_met) / len(measured) * 100 if measured else 0
    avg_improvement = (
        sum(m["improvementPct"] for m in measured if m["improvementPct"] is not None)
        / len(measured) if measured else 0
    )

    by_domain = {}
    for m in measured:
        domain = m["domain"] or "Unknown"
        if domain not in by_domain:
            by_domain[domain] = {"metrics": [], "avg_improvement": 0.0, "targets_met": 0}
        by_domain[domain]["metrics"].append(m)
    for domain, data in by_domain.items():
        improvements = [m["improvementPct"] for m in data["metrics"] if m["improvementPct"] is not None]
        data["avg_improvement"] = round(sum(improvements) / len(improvements), 1) if improvements else 0
        data["targets_met"]     = sum(1 for m in data["metrics"] if m["targetMet"])
        data["target_rate"]     = round(data["targets_met"] / len(data["metrics"]) * 100, 0)

    top_wins = sorted(
        [m for m in measured if m["improvementPct"] is not None],
        key=lambda x: x["improvementPct"],
        reverse=True
    )[:5]

    gaps = [m for m in measured if not m["targetMet"]]

    log.info("Impact analysis: %d metrics | %.1f%% coverage | %.1f%% targets met | avg improvement %.1f%%",
             len(metrics), coverage, target_rate, avg_improvement)

    return {
        "summary": {
            "totalMetrics":      len(metrics),
            "measuredMetrics":   len(measured),
            "unmeasuredMetrics": len(unmeasured),
            "coveragePct":       round(coverage, 1),
            "targetsMet":        len(targets_met),
            "targetsMissed":     len(targets_miss),
            "targetRatePct":     round(target_rate, 1),
            "avgImprovementPct": round(avg_improvement, 1),
        },
        "byDomain":   by_domain,
        "topWins":    top_wins,
        "gaps":       gaps,
        "unmeasured": [m["metric"] for m in unmeasured],
    }
