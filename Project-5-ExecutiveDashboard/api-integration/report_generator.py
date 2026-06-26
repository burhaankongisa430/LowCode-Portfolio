"""
Weekly Executive Report Generator.
Builds a self-contained HTML email that renders on desktop, mobile, and dark mode clients.
No external dependencies — no Matplotlib, no Jinja2.
Called by the scheduler every Monday morning.
"""

from datetime import datetime, timezone
from config import Config


def _score_color(score: float) -> str:
    if score >= 85: return "#27AE60"
    if score >= 70: return "#2ECC71"
    if score >= 55: return "#F39C12"
    if score >= 40: return "#E67E22"
    return "#E74C3C"


def _score_bar(score: float, width: int = 200) -> str:
    """ASCII-art-style bar rendered as an HTML div."""
    fill = int((score / 100) * width)
    color = _score_color(score)
    return (
        f"<div style='background:#ECF0F1;border-radius:4px;height:8px;width:{width}px;display:inline-block'>"
        f"<div style='background:{color};border-radius:4px;height:8px;width:{fill}px'></div></div>"
    )


def _domain_card(icon: str, label: str, score: float, weight: str, highlights: list[str]) -> str:
    color = _score_color(score)
    bullets = "".join(f"<li style='margin:2px 0;font-size:12px'>{h}</li>" for h in highlights)
    return f"""
<td style='vertical-align:top;padding:8px;width:25%'>
  <div style='background:#fff;border:1px solid #ECF0F1;border-radius:8px;padding:16px;border-top:4px solid {color}'>
    <div style='font-size:22px'>{icon}</div>
    <div style='font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#7F8C8D;margin:4px 0'>{label} <span style='font-size:10px'>({weight})</span></div>
    <div style='font-size:32px;font-weight:700;color:{color}'>{score:.0f}</div>
    <div style='font-size:11px;color:#95A5A6;margin-bottom:8px'>/100</div>
    {_score_bar(score, 150)}
    <ul style='margin:8px 0 0;padding-left:16px;color:#555'>{bullets}</ul>
  </div>
</td>"""


def _alert_rows(alerts: list[dict]) -> str:
    if not alerts:
        return "<tr><td colspan='4' style='padding:12px;text-align:center;color:#27AE60'>✅ No alerts — all KPIs within target ranges.</td></tr>"
    rows = ""
    for a in alerts:
        sev_color = "#E74C3C" if a["severity"] == "Critical" else "#F39C12"
        rows += (
            f"<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #ECF0F1'><span style='background:{sev_color};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold'>{a['severity']}</span></td>"
            f"<td style='padding:8px;border-bottom:1px solid #ECF0F1'>{a['domain']}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #ECF0F1'>{a['kpiName']}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #ECF0F1;color:{sev_color};font-weight:bold'>{a['currentValue']}</td>"
            f"</tr>"
        )
    return rows


def build_html(kpis: dict) -> str:
    """
    Generates the complete HTML executive report from a KPI dict.
    """
    now = datetime.now(timezone.utc)
    report_date = now.strftime("%A, %d %B %Y")
    generated_at = now.strftime("%H:%M UTC")
    health = kpis["health_score"]
    status = kpis["health_status"]
    health_color = _score_color(health)
    alerts = kpis.get("alerts", [])
    alert_count = len(alerts)
    critical_count = sum(1 for a in alerts if a["severity"] == "Critical")

    subject_emoji = "🚨" if critical_count > 0 else ("⚠" if alert_count > 0 else "✅")

    ops_highlights = [
        f"SLA Met Rate: {kpis['sla_met_rate']:.1f}%",
        f"Active Breaches: {kpis['active_breaches']}",
        f"Avg Resolution: {kpis['avg_resolution_hours']:.1f}h",
        f"Open Tickets: {kpis['open_tickets']}",
    ]
    crm_highlights = [
        f"Weighted Pipeline: R{kpis['weighted_pipeline']:,.0f}",
        f"Won MTD: R{kpis['won_revenue_mtd']:,.0f}",
        f"Win Rate: {kpis['win_rate']:.1f}%",
        f"Quota: {kpis['quota_attainment']:.1f}%",
    ]
    hr_highlights = [
        f"Active Onboarding: {kpis['active_onboarding']}",
        f"On Track: {kpis['onboarding_on_track_rate']:.1f}%",
        f"Avg Completion: {kpis['avg_completion_days']:.0f} days",
        f"Day 1 Readiness: {kpis['day1_readiness_rate']:.1f}%",
    ]
    fin_highlights = [
        f"Committed MTD: R{kpis['committed_spend_mtd']:,.0f}",
        f"Budget Util: {kpis['avg_budget_util']:.1f}%",
        f"Pending: {kpis['pending_approvals']}",
        f"Cycle Time: {kpis['approval_cycle_days']:.1f} days",
    ]

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weekly Executive KPI Report — {report_date}</title>
</head>
<body style="margin:0;padding:0;background:#F0F2F5;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F0F2F5;padding:24px 0">
<tr><td align="center">
<table width="680" cellpadding="0" cellspacing="0" style="max-width:680px;width:100%">

  <!-- HEADER -->
  <tr><td style="background:#2C3E50;padding:28px 32px;border-radius:8px 8px 0 0">
    <table width="100%"><tr>
      <td>
        <div style="color:#BDC3C7;font-size:12px;text-transform:uppercase;letter-spacing:1px">Weekly Executive Report</div>
        <div style="color:#fff;font-size:22px;font-weight:700;margin-top:4px">{Config.COMPANY_NAME}</div>
        <div style="color:#7F8C8D;font-size:13px;margin-top:2px">{report_date}</div>
      </td>
      <td align="right">
        <div style="color:{health_color};font-size:48px;font-weight:700;line-height:1">{health:.0f}</div>
        <div style="color:#BDC3C7;font-size:12px">Overall Health</div>
        <div style="color:{health_color};font-size:14px;font-weight:bold">{status}</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- ALERT BANNER -->
  {'<tr><td style="background:#E74C3C;padding:10px 32px;color:#fff;font-size:13px;font-weight:bold">🚨 ' + str(critical_count) + ' CRITICAL KPI alert(s) require immediate attention. See alerts section below.</td></tr>' if critical_count > 0 else (''.join(['<tr><td style="background:#F39C12;padding:10px 32px;color:#fff;font-size:13px">⚠ ' + str(alert_count) + ' KPI warning(s). Review alerts section.</td></tr>']) if alert_count > 0 else '<tr><td style="background:#27AE60;padding:10px 32px;color:#fff;font-size:13px">✅ All KPIs within target ranges this week.</td></tr>')}

  <!-- DOMAIN CARDS -->
  <tr><td style="background:#F8F9FA;padding:20px 24px">
    <div style="font-size:13px;color:#7F8C8D;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Domain Scores</div>
    <table width="100%" cellspacing="8">
    <tr>
      {_domain_card("⚙", "Operational", kpis["operational_score"], "25%", ops_highlights)}
      {_domain_card("💼", "Commercial", kpis["commercial_score"], "30%", crm_highlights)}
      {_domain_card("👥", "People", kpis["people_score"], "20%", hr_highlights)}
      {_domain_card("💰", "Finance", kpis["finance_score"], "25%", fin_highlights)}
    </tr>
    </table>
  </td></tr>

  <!-- ALERTS TABLE -->
  <tr><td style="background:#fff;padding:20px 32px">
    <div style="font-size:13px;font-weight:bold;margin-bottom:12px">KPI Alerts ({alert_count})</div>
    <table width="100%" cellspacing="0" style="border-collapse:collapse">
      <thead><tr style="background:#F8F9FA">
        <th style="padding:8px;text-align:left;font-size:12px;color:#7F8C8D">Severity</th>
        <th style="padding:8px;text-align:left;font-size:12px;color:#7F8C8D">Domain</th>
        <th style="padding:8px;text-align:left;font-size:12px;color:#7F8C8D">KPI</th>
        <th style="padding:8px;text-align:left;font-size:12px;color:#7F8C8D">Value</th>
      </tr></thead>
      <tbody>{_alert_rows(alerts)}</tbody>
    </table>
  </td></tr>

  <!-- DATA COVERAGE -->
  <tr><td style="background:#F8F9FA;padding:12px 32px;border-top:1px solid #ECF0F1">
    <div style="font-size:11px;color:#95A5A6">
      📡 Data from {kpis.get('domains_available', 4)}/4 source systems &nbsp;|&nbsp;
      Generated {generated_at} &nbsp;|&nbsp;
      ETL: {kpis.get('etl_duration_seconds', 0):.1f}s &nbsp;|&nbsp;
      <a href="https://app.powerbi.com/groups/{{workspaceId}}/dashboards/{{dashboardId}}" style="color:#3498DB">Open Live Dashboard</a>
    </div>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:#2C3E50;padding:16px 32px;border-radius:0 0 8px 8px;text-align:center">
    <div style="color:#7F8C8D;font-size:11px">
      This report is auto-generated by the {Config.COMPANY_NAME} Executive Dashboard platform.
      Scores refresh every 15 minutes. Reply to this email to unsubscribe.
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def get_subject(kpis: dict) -> str:
    health = kpis["health_score"]
    status = kpis["health_status"]
    alerts = kpis.get("alerts", [])
    critical = sum(1 for a in alerts if a["severity"] == "Critical")
    prefix = "🚨 CRITICAL — " if critical > 0 else ("⚠ " if alerts else "✅ ")
    return f"{prefix}Weekly KPI Report: {health:.0f}/100 ({status}) | {datetime.now(timezone.utc).strftime('%d %b %Y')}"
