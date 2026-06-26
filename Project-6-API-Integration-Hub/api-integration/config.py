import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Quickbase — Integration Hub app
    QB_REALM              = os.getenv("QB_REALM", "yourcompany.quickbase.com")
    QB_TOKEN              = os.getenv("QB_TOKEN", "")
    QB_EVENTS_TABLE       = os.getenv("QB_EVENTS_TABLE", "")
    QB_ROUTES_TABLE       = os.getenv("QB_ROUTES_TABLE", "")
    QB_DLQ_TABLE          = os.getenv("QB_DLQ_TABLE", "")
    QB_CREDENTIALS_TABLE  = os.getenv("QB_CREDENTIALS_TABLE", "")
    QB_HEALTH_TABLE       = os.getenv("QB_HEALTH_TABLE", "")

    # Target QB apps (for connector routing)
    QB_SD_TOKEN           = os.getenv("QB_SD_TOKEN", "")   # ServiceDeskAutomation
    QB_SD_TICKETS_TABLE   = os.getenv("QB_SD_TICKETS_TABLE", "")
    QB_CRM_TOKEN          = os.getenv("QB_CRM_TOKEN", "")  # CRM-System
    QB_CRM_CONTACTS_TABLE = os.getenv("QB_CRM_CONTACTS_TABLE", "")
    QB_CRM_DEALS_TABLE    = os.getenv("QB_CRM_DEALS_TABLE", "")
    QB_OB_TOKEN           = os.getenv("QB_OB_TOKEN", "")   # EmployeeOnboarding
    QB_OB_EMPLOYEES_TABLE = os.getenv("QB_OB_EMPLOYEES_TABLE", "")

    # BambooHR
    BAMBOOHR_API_KEY      = os.getenv("BAMBOOHR_API_KEY", "")
    BAMBOOHR_SUBDOMAIN    = os.getenv("BAMBOOHR_SUBDOMAIN", "yourcompany")
    BAMBOOHR_WEBHOOK_SECRET = os.getenv("BAMBOOHR_WEBHOOK_SECRET", "")

    # Jira
    JIRA_BASE_URL         = os.getenv("JIRA_BASE_URL", "https://yourcompany.atlassian.net")
    JIRA_EMAIL            = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN        = os.getenv("JIRA_API_TOKEN", "")
    JIRA_WEBHOOK_SECRET   = os.getenv("JIRA_WEBHOOK_SECRET", "")
    JIRA_SD_PROJECT       = os.getenv("JIRA_SD_PROJECT", "SD")

    # Microsoft Teams
    TEAMS_WEBHOOK_URL     = os.getenv("TEAMS_WEBHOOK_URL", "")

    # App
    WEBHOOK_SECRET        = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG                 = os.getenv("DEBUG", "false").lower() == "true"
    PORT                  = int(os.getenv("PORT", 5005))

    # Rate limits (requests per minute per source)
    RATE_LIMITS = {
        "bamboohr":   60,
        "jira":       120,
        "salesforce": 60,
        "web_form":   300,
        "quickbase":  100,
        "default":    60,
    }

    # Retry config
    MAX_RETRIES       = 5
    RETRY_BASE_DELAY  = 1.0   # seconds
    RETRY_MAX_DELAY   = 30.0  # seconds
    RETRY_JITTER_PCT  = 0.20  # ± 20% jitter

    # Deduplication window
    DEDUP_WINDOW_SECONDS = 60
