"""
Dataverse loader — writes KPI snapshots to Microsoft Dataverse
via the Web API, enabling Power BI DirectQuery with near-real-time refresh.

Uses MSAL client credentials (app-only) with the Dataverse scope.
"""

import logging
import requests
import msal
from config import Config

log = logging.getLogger(__name__)
DATAVERSE_SCOPE = [f"{Config.DATAVERSE_ENV_URL}/.default"]


def _get_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=Config.GRAPH_CLIENT_ID,
        client_credential=Config.GRAPH_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{Config.GRAPH_TENANT_ID}",
    )
    result = app.acquire_token_for_client(scopes=DATAVERSE_SCOPE)
    if "access_token" not in result:
        raise RuntimeError(f"Dataverse token error: {result.get('error_description', 'unknown')}")
    return result["access_token"]


def _api_url(path: str) -> str:
    return f"{Config.DATAVERSE_ENV_URL.rstrip('/')}/api/data/v9.2/{path.lstrip('/')}"


def _post(path: str, body: dict, token: str) -> dict | None:
    headers = {
        "Authorization":   f"Bearer {token}",
        "Content-Type":    "application/json",
        "OData-MaxVersion":"4.0",
        "OData-Version":   "4.0",
        "Prefer":          "return=representation",
    }
    r = requests.post(_api_url(path), headers=headers, json=body, timeout=15)
    if r.status_code in (200, 201, 204):
        return r.json() if r.content else None
    r.raise_for_status()


def write_snapshot(kpis: dict) -> bool:
    """
    Write a KPI snapshot to the Dataverse cr_kpi_snapshots table.
    Returns True on success.
    """
    try:
        token = _get_token()
        body = {
            "cr_snapshot_time":          kpis["snapshot_time"],
            "cr_health_score":           kpis["health_score"],
            "cr_health_status":          kpis["health_status"],
            "cr_operational_score":      kpis["operational_score"],
            "cr_commercial_score":       kpis["commercial_score"],
            "cr_people_score":           kpis["people_score"],
            "cr_finance_score":          kpis["finance_score"],
            "cr_sla_met_rate":           kpis["sla_met_rate"],
            "cr_active_breaches":        kpis["active_breaches"],
            "cr_avg_resolution_hours":   kpis["avg_resolution_hours"],
            "cr_open_tickets":           kpis["open_tickets"],
            "cr_weighted_pipeline":      kpis["weighted_pipeline"],
            "cr_won_revenue_mtd":        kpis["won_revenue_mtd"],
            "cr_win_rate":               kpis["win_rate"],
            "cr_quota_attainment":       kpis["quota_attainment"],
            "cr_stalled_deals":          kpis["stalled_deals"],
            "cr_active_onboarding":      kpis["active_onboarding"],
            "cr_onboarding_on_track":    kpis["onboarding_on_track_rate"],
            "cr_avg_completion_days":    kpis["avg_completion_days"],
            "cr_day1_readiness_rate":    kpis["day1_readiness_rate"],
            "cr_committed_spend_mtd":    kpis["committed_spend_mtd"],
            "cr_avg_budget_util":        kpis["avg_budget_util"],
            "cr_pending_approvals":      kpis["pending_approvals"],
            "cr_approval_cycle_days":    kpis["approval_cycle_days"],
            "cr_domains_available":      kpis["domains_available"],
            "cr_alert_count":            len(kpis.get("alerts", [])),
        }
        _post("cr_kpi_snapshots", body, token)
        log.info("KPI snapshot written to Dataverse (health=%.1f)", kpis["health_score"])

        # Write individual alert records
        for alert in kpis.get("alerts", []):
            _post("cr_kpi_alerts", {
                "cr_alert_time":      kpis["snapshot_time"],
                "cr_domain":          alert["domain"],
                "cr_kpi_name":        alert["kpiName"],
                "cr_current_value":   alert["currentValue"],
                "cr_threshold_value": alert["thresholdValue"],
                "cr_severity":        alert["severity"],
                "cr_message":         alert["message"],
                "cr_acknowledged":    False,
            }, token)

        return True

    except Exception as exc:
        log.error("Dataverse write failed: %s", exc)
        return False
