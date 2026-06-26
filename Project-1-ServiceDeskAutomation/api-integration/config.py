import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Quickbase
    QB_REALM_HOSTNAME = os.getenv("QB_REALM_HOSTNAME", "yourcompany.quickbase.com")
    QB_USER_TOKEN = os.getenv("QB_USER_TOKEN", "")
    QB_APP_ID = os.getenv("QB_APP_ID", "")
    QB_TICKETS_TABLE_ID = os.getenv("QB_TICKETS_TABLE_ID", "")
    QB_AGENTS_TABLE_ID = os.getenv("QB_AGENTS_TABLE_ID", "")
    QB_AUDIT_TABLE_ID = os.getenv("QB_AUDIT_TABLE_ID", "")

    # Microsoft Teams
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
    TEAMS_ESCALATION_WEBHOOK_URL = os.getenv("TEAMS_ESCALATION_WEBHOOK_URL", "")

    # Power Automate
    PA_INTAKE_FLOW_URL = os.getenv("PA_INTAKE_FLOW_URL", "")
    PA_ROUTING_FLOW_URL = os.getenv("PA_ROUTING_FLOW_URL", "")
    PA_ESCALATION_FLOW_URL = os.getenv("PA_ESCALATION_FLOW_URL", "")

    # App
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", 5000))

    # SLA in hours
    SLA_POLICIES = {
        "P1-Critical": {"response": 1,  "resolution": 4,  "escalation_l1": 2,  "escalation_l2": 3},
        "P2-High":     {"response": 4,  "resolution": 8,  "escalation_l1": 6,  "escalation_l2": 7},
        "P3-Medium":   {"response": 8,  "resolution": 24, "escalation_l1": 18, "escalation_l2": 22},
        "P4-Low":      {"response": 24, "resolution": 72, "escalation_l1": 48, "escalation_l2": 60},
    }

    VALID_PRIORITIES = list(SLA_POLICIES.keys())
    VALID_STATUSES = ["New", "Assigned", "In Progress", "Pending", "Resolved", "Closed"]
    VALID_CATEGORIES = [
        "IT-Hardware", "IT-Software", "IT-Network",
        "HR-Leave", "HR-Payroll", "HR-Benefits",
        "Finance-Invoice", "Finance-Expense",
        "Facilities",
    ]
    CATEGORY_TO_TEAM = {
        "IT-Hardware": "IT Support", "IT-Software": "IT Support", "IT-Network": "IT Support",
        "HR-Leave": "HR", "HR-Payroll": "HR", "HR-Benefits": "HR",
        "Finance-Invoice": "Finance", "Finance-Expense": "Finance",
        "Facilities": "Facilities",
    }
