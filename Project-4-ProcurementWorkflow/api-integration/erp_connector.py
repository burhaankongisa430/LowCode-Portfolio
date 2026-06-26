"""
ERP / Finance system connector.
Pushes approved Purchase Orders to the organization's ERP system
via its REST API, so Finance has a single source of truth for payments.

Designed to be ERP-agnostic: the _push method is the only place that
needs updating when switching ERP vendors (SAP, Oracle, Sage, etc.).
"""

import logging
import requests
from config import Config

log = logging.getLogger(__name__)


class ERPConnector:

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {Config.ERP_API_KEY}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        })

    def _push(self, payload: dict) -> dict:
        url = f"{Config.ERP_BASE_URL.rstrip('/')}{Config.ERP_PO_ENDPOINT}"
        r = self._session.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    def sync_po(self, po: dict) -> dict:
        """
        Push an approved PO to the ERP system.

        po keys required: poNumber, requestNumber, vendorName, vendorEmail,
                          amount, currency, budgetCode, department,
                          paymentTerms, issueDate, approvedBy

        Returns: {"erpReference": str, "synced": bool, "error": str | None}
        """
        erp_payload = {
            "external_ref":    po["poNumber"],
            "pr_reference":    po.get("requestNumber", ""),
            "vendor_name":     po.get("vendorName", ""),
            "vendor_email":    po.get("vendorEmail", ""),
            "total_amount":    float(po.get("amount", 0)),
            "currency_code":   po.get("currency", "ZAR"),
            "gl_code":         po.get("budgetCode", ""),
            "cost_center":     po.get("department", ""),
            "payment_terms":   po.get("paymentTerms", "Net 30"),
            "issue_date":      po.get("issueDate", ""),
            "authorized_by":   po.get("approvedBy", ""),
            "description":     po.get("title", ""),
            "status":          "open",
        }

        try:
            response = self._push(erp_payload)
            erp_ref = response.get("id") or response.get("reference") or po["poNumber"]
            log.info("PO %s synced to ERP — ERP ref: %s", po["poNumber"], erp_ref)
            return {"erpReference": str(erp_ref), "synced": True, "error": None}

        except requests.HTTPError as exc:
            log.error("ERP sync failed for %s: %s", po.get("poNumber"), exc)
            return {"erpReference": "", "synced": False, "error": str(exc)}

        except requests.RequestException as exc:
            log.error("ERP connection error: %s", exc)
            return {"erpReference": "", "synced": False, "error": f"Connection error: {exc}"}

    def get_payment_status(self, erp_reference: str) -> dict:
        """
        Poll the ERP for the payment status of a PO.
        Used by the optional three-way match module.
        """
        try:
            url = f"{Config.ERP_BASE_URL.rstrip('/')}{Config.ERP_PO_ENDPOINT}/{erp_reference}"
            r = self._session.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            return {
                "status":        data.get("status", "unknown"),
                "invoiceNumber": data.get("invoice_number", ""),
                "invoiceAmount": float(data.get("invoice_amount", 0)),
                "paidDate":      data.get("paid_date", ""),
            }
        except Exception as exc:
            log.error("Payment status fetch failed for %s: %s", erp_reference, exc)
            return {"status": "error", "error": str(exc)}
