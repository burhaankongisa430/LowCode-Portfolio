import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Quickbase
    QB_REALM_HOSTNAME      = os.getenv("QB_REALM_HOSTNAME", "yourcompany.quickbase.com")
    QB_USER_TOKEN          = os.getenv("QB_USER_TOKEN", "")
    QB_APP_ID              = os.getenv("QB_APP_ID", "")
    QB_REQUESTS_TABLE      = os.getenv("QB_REQUESTS_TABLE", "")
    QB_VENDORS_TABLE       = os.getenv("QB_VENDORS_TABLE", "")
    QB_BUDGETS_TABLE       = os.getenv("QB_BUDGETS_TABLE", "")
    QB_APPROVAL_HIST_TABLE = os.getenv("QB_APPROVAL_HIST_TABLE", "")
    QB_PO_TABLE            = os.getenv("QB_PO_TABLE", "")
    QB_APPROVERS_TABLE     = os.getenv("QB_APPROVERS_TABLE", "")

    # ERP / Finance system
    ERP_BASE_URL    = os.getenv("ERP_BASE_URL", "https://erp.yourcompany.com/api/v1")
    ERP_API_KEY     = os.getenv("ERP_API_KEY", "")
    ERP_PO_ENDPOINT = os.getenv("ERP_PO_ENDPOINT", "/purchase-orders")

    # Company details (used in PO generation)
    COMPANY_NAME    = os.getenv("COMPANY_NAME", "Your Company (Pty) Ltd")
    COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "123 Business Park, Cape Town, 8001")
    COMPANY_VAT     = os.getenv("COMPANY_VAT", "4730123456")
    COMPANY_REG     = os.getenv("COMPANY_REG", "2001/123456/07")
    COMPANY_EMAIL   = os.getenv("COMPANY_EMAIL", "procurement@yourcompany.com")
    COMPANY_PHONE   = os.getenv("COMPANY_PHONE", "+27 21 123 4567")

    # App
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG          = os.getenv("DEBUG", "false").lower() == "true"
    PORT           = int(os.getenv("PORT", 5003))

    # Approval thresholds (ZAR)
    APPROVAL_THRESHOLDS = {
        1: {"label": "Manager",          "max": 75_000},
        2: {"label": "Department Head",   "max": 250_000},
        3: {"label": "Finance Director",  "max": 750_000},
        4: {"label": "CEO",               "max": float("inf")},
    }

    VALID_STATUSES = [
        "Draft", "Submitted", "Under Review",
        "Level 1 Pending", "Level 2 Pending", "Level 3 Pending", "Level 4 Pending",
        "Approved", "Rejected", "PO Issued", "Canceled",
    ]
