"""
Purchase Order generator.
Builds a professional HTML PO document from request data,
creates the PO record in Quickbase, and returns the HTML for emailing.

The HTML is structured for clean browser printing (A4 @media print).
To generate a PDF instead: install weasyprint and call
  weasyprint.HTML(string=html).write_pdf()
"""

import logging
from datetime import datetime, timezone, timedelta
from config import Config

log = logging.getLogger(__name__)


def _format_currency(amount: float, currency: str = "ZAR") -> str:
    symbol = {"ZAR": "R", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def _next_30_days() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%d %B %Y")


def build_po_html(po: dict) -> str:
    """
    Generate a complete HTML purchase order document.

    po keys: poNumber, requestNumber, issueDate, title, totalAmount, currency,
             vendorName, vendorEmail, department, budgetCode, paymentTerms,
             deliveryAddress, requestorName, approvedBy, approvalDate
    """
    amount_formatted = _format_currency(
        float(po.get("totalAmount", 0)),
        po.get("currency", "ZAR")
    )
    issue_date = datetime.now(timezone.utc).strftime("%d %B %Y")
    delivery_due = po.get("deliveryDate", _next_30_days())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', Arial, sans-serif; font-size: 13px; color: #2C3E50; background: #fff; }}
  .po-container {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #2C3E50; padding-bottom: 20px; margin-bottom: 24px; }}
  .company-name {{ font-size: 22px; font-weight: 700; color: #2C3E50; }}
  .company-details {{ font-size: 11px; color: #7F8C8D; margin-top: 4px; line-height: 1.6; }}
  .po-title {{ text-align: right; }}
  .po-title h1 {{ font-size: 28px; font-weight: 700; color: #2C3E50; letter-spacing: 2px; }}
  .po-number {{ font-size: 16px; color: #E74C3C; font-weight: 600; margin-top: 4px; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  .meta-box {{ background: #F8F9FA; border-radius: 6px; padding: 16px; }}
  .meta-box h3 {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #7F8C8D; margin-bottom: 8px; }}
  .meta-box p {{ font-size: 13px; font-weight: 600; line-height: 1.8; }}
  .meta-box .label {{ font-weight: 400; color: #7F8C8D; font-size: 11px; }}
  table.items {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
  table.items thead tr {{ background: #2C3E50; color: #fff; }}
  table.items thead th {{ padding: 10px 12px; text-align: left; font-size: 12px; }}
  table.items tbody tr {{ border-bottom: 1px solid #ECF0F1; }}
  table.items tbody td {{ padding: 12px; }}
  table.items tbody tr:nth-child(even) {{ background: #F8F9FA; }}
  .total-row {{ background: #2C3E50 !important; color: #fff; }}
  .total-row td {{ font-size: 15px; font-weight: 700; padding: 14px 12px !important; }}
  .footer-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; }}
  .terms-box {{ font-size: 11px; color: #7F8C8D; line-height: 1.8; }}
  .approval-box {{ background: #EAFAF1; border: 1px solid #27AE60; border-radius: 6px; padding: 16px; }}
  .approval-box h3 {{ color: #27AE60; font-size: 12px; margin-bottom: 8px; }}
  .approval-box p {{ font-size: 12px; line-height: 1.8; }}
  .watermark {{ text-align: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid #ECF0F1; font-size: 11px; color: #BDC3C7; }}
  @media print {{ .po-container {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="po-container">

  <div class="header">
    <div>
      <div class="company-name">{Config.COMPANY_NAME}</div>
      <div class="company-details">
        {Config.COMPANY_ADDRESS}<br>
        VAT Reg: {Config.COMPANY_VAT} &nbsp;|&nbsp; Reg No: {Config.COMPANY_REG}<br>
        {Config.COMPANY_EMAIL} &nbsp;|&nbsp; {Config.COMPANY_PHONE}
      </div>
    </div>
    <div class="po-title">
      <h1>PURCHASE ORDER</h1>
      <div class="po-number">{po.get('poNumber', 'PO-000000')}</div>
    </div>
  </div>

  <div class="meta-grid">
    <div class="meta-box">
      <h3>Vendor / Supplier</h3>
      <p>
        <strong>{po.get('vendorName', '—')}</strong><br>
        <span class="label">Email:</span> {po.get('vendorEmail', '—')}<br>
        <span class="label">Payment Terms:</span> {po.get('paymentTerms', 'Net 30')}
      </p>
    </div>
    <div class="meta-box">
      <h3>PO Details</h3>
      <p>
        <span class="label">Issue Date:</span> {issue_date}<br>
        <span class="label">Required By:</span> {delivery_due}<br>
        <span class="label">Budget Code:</span> {po.get('budgetCode', '—')}<br>
        <span class="label">Department:</span> {po.get('department', '—')}
      </p>
    </div>
    <div class="meta-box">
      <h3>Delivery Address</h3>
      <p>{po.get('deliveryAddress', Config.COMPANY_ADDRESS).replace(chr(10), '<br>')}</p>
    </div>
    <div class="meta-box">
      <h3>Requestor</h3>
      <p>
        <strong>{po.get('requestorName', '—')}</strong><br>
        <span class="label">PR Reference:</span> {po.get('requestNumber', '—')}
      </p>
    </div>
  </div>

  <table class="items">
    <thead>
      <tr>
        <th style="width:5%">#</th>
        <th style="width:55%">Description</th>
        <th style="width:15%">Qty</th>
        <th style="width:25%;text-align:right">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td>{po.get('title', 'Goods/Services as per agreed specification')}</td>
        <td>1</td>
        <td style="text-align:right">{amount_formatted}</td>
      </tr>
      <tr class="total-row">
        <td colspan="3" style="text-align:right">TOTAL ({po.get('currency','ZAR')})</td>
        <td style="text-align:right">{amount_formatted}</td>
      </tr>
    </tbody>
  </table>

  <div class="footer-grid">
    <div class="terms-box">
      <strong>Terms & Conditions</strong><br>
      1. All invoices must quote PO number {po.get('poNumber', '')}.<br>
      2. Goods/services must match this PO specification exactly.<br>
      3. Payment will be processed within {po.get('paymentTerms','Net 30').replace('Net ','').replace('EOM','30 days of month end')} days of receiving a valid tax invoice.<br>
      4. Delivery must be completed by {delivery_due}.<br>
      5. {Config.COMPANY_NAME} reserves the right to return goods that do not meet specification.
    </div>
    <div class="approval-box">
      <h3>✅ Authorization</h3>
      <p>
        <strong>Approved By:</strong> {po.get('approvedBy', '—')}<br>
        <strong>Approval Date:</strong> {datetime.now(timezone.utc).strftime('%d %B %Y')}<br>
        <strong>PR Reference:</strong> {po.get('requestNumber', '—')}
      </p>
    </div>
  </div>

  <div class="watermark">
    This is a system-generated Purchase Order. Questions: {Config.COMPANY_EMAIL}
  </div>

</div>
</body>
</html>"""


def generate_and_save(po_data: dict, qb_client) -> dict:
    """
    Build the PO HTML, save the PO record to Quickbase, and return identifiers.

    Returns: {"poNumber": str, "poRecordId": int, "poHtml": str}
    """
    html = build_po_html(po_data)

    try:
        result = qb_client.create_po_record(
            request_record_id=po_data["requestRecordId"],
            po_data=po_data,
            html=html,
        )
        po_number = result.get("poNumber", "PO-000000")
        po_record_id = result.get("recordId", 0)

        # Insert PO number into HTML now that we have it
        html = html.replace("PO-000000", po_number)

        log.info("Generated PO %s for request %s", po_number, po_data.get("requestNumber"))
        return {"poNumber": po_number, "poRecordId": po_record_id, "poHtml": html}

    except Exception as exc:
        log.error("PO creation failed: %s", exc)
        raise
