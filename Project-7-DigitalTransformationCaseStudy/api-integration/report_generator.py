"""
Executive Transformation Report Generator.
Produces the monthly HTML report combining ROI financials,
process improvement highlights, and program status.
"""

from datetime import datetime, timezone
from roi_calculator import ProgramROI
from config import Config


def _currency(amount: float, symbol: str = "R") -> str:
    return f"{symbol}{amount:,.0f}"


def _pct(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}%"


def _rag_color(value: float, green: float, amber: float, higher_is_better: bool = True) -> str:
    if higher_is_better:
        if value >= green: return "#27AE60"
        if value >= amber: return "#F39C12"
        return "#E74C3C"
    else:
        if value <= green: return "#27AE60"
        if value <= amber: return "#F39C12"
        return "#E74C3C"


def _initiative_rows(roi: ProgramROI) -> str:
    rows = ""
    for init in roi.initiative_rois:
        roi_color = _rag_color(init.roi_pct, 150, 50)
        real_color = _rag_color(init.realization_pct, 85, 70)
        rows += f"""
        <tr>
          <td style='padding:8px;font-weight:bold'>{init.name}</td>
          <td style='padding:8px;text-align:center'>{init.domain}</td>
          <td style='padding:8px;text-align:right'>{_currency(init.investment)}</td>
          <td style='padding:8px;text-align:right;color:{roi_color};font-weight:bold'>{_pct(init.roi_pct, 0)}</td>
          <td style='padding:8px;text-align:center'>{init.payback_months:.1f} mo</td>
          <td style='padding:8px;text-align:right'>{_currency(init.npv_3yr)}</td>
          <td style='padding:8px;text-align:center;color:{real_color};font-weight:bold'>{_pct(init.realization_pct, 0)}</td>
        </tr>"""
    return rows


def _benefit_category_rows(roi: ProgramROI) -> str:
    rows = ""
    for cat in roi.benefit_categories:
        conf_bar = int(cat.confidence * 100)
        conf_color = _rag_color(cat.confidence * 100, 80, 60)
        rows += f"""
        <tr>
          <td style='padding:8px;font-weight:bold'>{cat.name}</td>
          <td style='padding:8px;text-align:right;color:#27AE60;font-weight:bold'>{_currency(cat.annual_value)}</td>
          <td style='padding:8px;font-size:12px;color:#7F8C8D'>{cat.description}</td>
          <td style='padding:8px;text-align:center'>
            <div style='background:#ECF0F1;border-radius:4px;height:8px;width:80px;display:inline-block'>
              <div style='background:{conf_color};border-radius:4px;height:8px;width:{conf_bar * 0.8}px'></div>
            </div>
            <span style='font-size:11px;color:#7F8C8D;margin-left:4px'>{conf_bar}%</span>
          </td>
        </tr>"""
    return rows


def _sensitivity_cards(roi: ProgramROI) -> str:
    cards = ""
    colors = {"pessimistic": "#E67E22", "base": "#27AE60", "optimistic": "#1ABC9C"}
    for key, data in roi.sensitivity.items():
        color = colors.get(key, "#95A5A6")
        cards += f"""
        <td style='width:33%;padding:8px;vertical-align:top'>
          <div style='border:1px solid #ECF0F1;border-top:4px solid {color};border-radius:6px;padding:16px;text-align:center'>
            <div style='font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#7F8C8D'>{data['label']}</div>
            <div style='font-size:28px;font-weight:700;color:{color};margin:8px 0'>{_pct(data['roi_pct'], 0)}</div>
            <div style='font-size:12px;color:#555'>{_currency(data['annual'])}/yr</div>
            <div style='font-size:12px;color:#555'>Payback: {data['payback']} months</div>
            <div style='font-size:12px;color:#555'>NPV: {_currency(data['npv_3yr'])}</div>
          </div>
        </td>"""
    return cards


def build_html(roi: ProgramROI, impact_summary: dict = None) -> str:
    now = datetime.now(timezone.utc)
    report_date = now.strftime("%B %Y")
    roi_color     = _rag_color(roi.program_roi_pct, 150, 50)
    real_color    = _rag_color(roi.benefit_realization_pct, 85, 70)
    payback_color = _rag_color(roi.program_payback_months, 6, 12, higher_is_better=False)

    top_wins_html = ""
    if impact_summary and impact_summary.get("topWins"):
        for win in impact_summary["topWins"][:3]:
            top_wins_html += f"<li><b>{win['metric']}</b>: {_pct(win['improvementPct'], 0)} improvement (before: {win['before']} {win['unit']} → after: {win['after']} {win['unit']})</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Transformation ROI Report — {report_date}</title></head>
<body style="margin:0;padding:0;background:#F0F2F5;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F0F2F5;padding:24px 0">
<tr><td align="center">
<table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%">

  <!-- HEADER -->
  <tr><td style="background:#2C3E50;padding:28px 32px;border-radius:8px 8px 0 0">
    <table width="100%"><tr>
      <td>
        <div style="color:#BDC3C7;font-size:12px;text-transform:uppercase;letter-spacing:1px">Digital Transformation Program</div>
        <div style="color:#fff;font-size:20px;font-weight:700;margin-top:4px">{Config.COMPANY_NAME}</div>
        <div style="color:#7F8C8D;font-size:13px">Monthly ROI Report — {report_date}</div>
      </td>
      <td align="right">
        <div style="color:{roi_color};font-size:52px;font-weight:700;line-height:1">{_pct(roi.program_roi_pct, 0)}</div>
        <div style="color:#BDC3C7;font-size:12px">Program ROI</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- HEADLINE KPIs -->
  <tr><td style="background:#fff;padding:20px 32px">
    <table width="100%" cellspacing="8"><tr>
      <td style="text-align:center;padding:12px;border-right:1px solid #ECF0F1">
        <div style="font-size:11px;color:#7F8C8D;text-transform:uppercase">Total Benefits YTD</div>
        <div style="font-size:24px;font-weight:700;color:#27AE60">{_currency(roi.total_actual_ytd)}</div>
      </td>
      <td style="text-align:center;padding:12px;border-right:1px solid #ECF0F1">
        <div style="font-size:11px;color:#7F8C8D;text-transform:uppercase">Investment</div>
        <div style="font-size:24px;font-weight:700;color:#2C3E50">{_currency(roi.total_investment)}</div>
      </td>
      <td style="text-align:center;padding:12px;border-right:1px solid #ECF0F1">
        <div style="font-size:11px;color:#7F8C8D;text-transform:uppercase">Payback Period</div>
        <div style="font-size:24px;font-weight:700;color:{payback_color}">{roi.program_payback_months:.1f} months</div>
      </td>
      <td style="text-align:center;padding:12px;border-right:1px solid #ECF0F1">
        <div style="font-size:11px;color:#7F8C8D;text-transform:uppercase">3-Year NPV</div>
        <div style="font-size:24px;font-weight:700;color:#2980B9">{_currency(roi.program_npv_3yr)}</div>
      </td>
      <td style="text-align:center;padding:12px">
        <div style="font-size:11px;color:#7F8C8D;text-transform:uppercase">Benefit Realization</div>
        <div style="font-size:24px;font-weight:700;color:{real_color}">{_pct(roi.benefit_realization_pct, 0)}</div>
        <div style="font-size:11px;color:{real_color}">{roi.realization_status}</div>
      </td>
    </tr></table>
  </td></tr>

  <!-- INITIATIVE ROI TABLE -->
  <tr><td style="background:#F8F9FA;padding:20px 32px">
    <div style="font-size:13px;font-weight:bold;margin-bottom:12px">ROI by Initiative</div>
    <table width="100%" style="border-collapse:collapse">
      <thead><tr style="background:#2C3E50;color:#fff">
        <th style="padding:8px;text-align:left">Initiative</th>
        <th style="padding:8px">Domain</th>
        <th style="padding:8px;text-align:right">Investment</th>
        <th style="padding:8px;text-align:right">ROI</th>
        <th style="padding:8px">Payback</th>
        <th style="padding:8px;text-align:right">3yr NPV</th>
        <th style="padding:8px">Realization</th>
      </tr></thead>
      <tbody>{_initiative_rows(roi)}</tbody>
    </table>
  </td></tr>

  <!-- BENEFIT CATEGORIES -->
  <tr><td style="background:#fff;padding:20px 32px">
    <div style="font-size:13px;font-weight:bold;margin-bottom:12px">Benefit Categories (Annual)</div>
    <table width="100%" style="border-collapse:collapse">
      <thead><tr style="background:#F8F9FA">
        <th style="padding:8px;text-align:left;font-size:12px;color:#7F8C8D">Category</th>
        <th style="padding:8px;text-align:right;font-size:12px;color:#7F8C8D">Annual Value</th>
        <th style="padding:8px;text-align:left;font-size:12px;color:#7F8C8D">Description</th>
        <th style="padding:8px;text-align:center;font-size:12px;color:#7F8C8D">Confidence</th>
      </tr></thead>
      <tbody>{_benefit_category_rows(roi)}</tbody>
      <tfoot><tr style="background:#2C3E50;color:#fff">
        <td style="padding:10px;font-weight:bold">TOTAL ANNUAL BENEFIT</td>
        <td style="padding:10px;text-align:right;font-weight:bold;font-size:16px">{_currency(roi.total_actual_annual)}</td>
        <td colspan="2" style="padding:10px;font-size:12px;color:#BDC3C7">Weighted confidence: {_pct(sum(c.annual_value * c.confidence for c in roi.benefit_categories) / roi.total_actual_annual * 100, 0)}</td>
      </tr></tfoot>
    </table>
  </td></tr>

  <!-- TOP PROCESS IMPROVEMENTS -->
  {"<tr><td style='background:#F8F9FA;padding:20px 32px'><div style='font-size:13px;font-weight:bold;margin-bottom:12px'>Top Process Improvements</div><ul style='margin:0;padding-left:20px;color:#555;font-size:13px;line-height:2'>" + top_wins_html + "</ul></td></tr>" if top_wins_html else ""}

  <!-- SENSITIVITY ANALYSIS -->
  <tr><td style="background:#fff;padding:20px 32px">
    <div style="font-size:13px;font-weight:bold;margin-bottom:12px">Sensitivity Analysis</div>
    <table width="100%" cellspacing="8"><tr>{_sensitivity_cards(roi)}</tr></table>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:#2C3E50;padding:16px 32px;border-radius:0 0 8px 8px;text-align:center">
    <div style="color:#7F8C8D;font-size:11px">
      Auto-generated by the Transformation Intelligence Platform · {report_date} ·
      All figures in ZAR · Methodology: docs/roi-methodology.md
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def get_subject(roi: ProgramROI) -> str:
    status_emoji = "✅" if roi.realization_status in ("Exceeding", "On Track") else "⚠"
    return (
        f"{status_emoji} Transformation ROI Report — "
        f"{datetime.now(timezone.utc).strftime('%B %Y')} | "
        f"ROI: {_pct(roi.program_roi_pct, 0)} | "
        f"Realization: {_pct(roi.benefit_realization_pct, 0)}"
    )
