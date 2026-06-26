import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Quickbase
    QB_REALM_HOSTNAME         = os.getenv("QB_REALM_HOSTNAME", "yourcompany.quickbase.com")
    QB_USER_TOKEN             = os.getenv("QB_USER_TOKEN", "")
    QB_APP_ID                 = os.getenv("QB_APP_ID", "")
    QB_EMPLOYEES_TABLE        = os.getenv("QB_EMPLOYEES_TABLE", "")
    QB_TASKS_TABLE            = os.getenv("QB_TASKS_TABLE", "")
    QB_TASK_TEMPLATES_TABLE   = os.getenv("QB_TASK_TEMPLATES_TABLE", "")
    QB_PLANS_TABLE            = os.getenv("QB_PLANS_TABLE", "")
    QB_DEPARTMENTS_TABLE      = os.getenv("QB_DEPARTMENTS_TABLE", "")
    QB_EQUIPMENT_TABLE        = os.getenv("QB_EQUIPMENT_TABLE", "")

    # Microsoft Graph (Azure AD provisioning + email sync)
    GRAPH_TENANT_ID     = os.getenv("GRAPH_TENANT_ID", "")
    GRAPH_CLIENT_ID     = os.getenv("GRAPH_CLIENT_ID", "")
    GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
    GRAPH_SCOPES        = ["https://graph.microsoft.com/.default"]
    AD_DOMAIN           = os.getenv("AD_DOMAIN", "yourcompany.com")

    # Power Automate flows
    PA_KICKOFF_FLOW_URL     = os.getenv("PA_KICKOFF_FLOW_URL", "")
    PA_MILESTONE_FLOW_URL   = os.getenv("PA_MILESTONE_FLOW_URL", "")

    # App
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG          = os.getenv("DEBUG", "false").lower() == "true"
    PORT           = int(os.getenv("PORT", 5002))

    # Default M365 licenses to assign (product SKU IDs)
    M365_LICENCE_SKUS = {
        "Permanent": os.getenv("M365_LICENCE_PERMANENT_SKU", ""),
        "Contract":  os.getenv("M365_LICENCE_CONTRACT_SKU", ""),
        "Intern":    os.getenv("M365_LICENCE_INTERN_SKU", ""),
    }

    # Role → Owner field mapping when resolving task owners from hire record
    OWNER_ROLE_EMAIL_MAP = {
        "IT":         "it-provisioning@yourcompany.com",
        "HR":         "hr@yourcompany.com",
        "Facilities": "facilities@yourcompany.com",
        "Manager":    None,   # resolved from hire record
        "Buddy":      None,   # resolved from hire record
        "New Hire":   None,   # resolved from hire record
    }
