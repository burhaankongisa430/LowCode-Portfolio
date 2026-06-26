import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Quickbase
    QB_REALM_HOSTNAME    = os.getenv("QB_REALM_HOSTNAME", "yourcompany.quickbase.com")
    QB_USER_TOKEN        = os.getenv("QB_USER_TOKEN", "")
    QB_APP_ID            = os.getenv("QB_APP_ID", "")
    QB_CONTACTS_TABLE    = os.getenv("QB_CONTACTS_TABLE", "")
    QB_COMPANIES_TABLE   = os.getenv("QB_COMPANIES_TABLE", "")
    QB_DEALS_TABLE       = os.getenv("QB_DEALS_TABLE", "")
    QB_ACTIVITIES_TABLE  = os.getenv("QB_ACTIVITIES_TABLE", "")
    QB_REPS_TABLE        = os.getenv("QB_REPS_TABLE", "")

    # Microsoft Graph API (for email/calendar activity sync)
    GRAPH_TENANT_ID      = os.getenv("GRAPH_TENANT_ID", "")
    GRAPH_CLIENT_ID      = os.getenv("GRAPH_CLIENT_ID", "")
    GRAPH_CLIENT_SECRET  = os.getenv("GRAPH_CLIENT_SECRET", "")
    GRAPH_SCOPES         = ["https://graph.microsoft.com/.default"]

    # Power Automate flows
    PA_LEAD_INTAKE_URL         = os.getenv("PA_LEAD_INTAKE_URL", "")
    PA_STAGE_PROGRESSION_URL   = os.getenv("PA_STAGE_PROGRESSION_URL", "")

    # App
    WEBHOOK_SECRET  = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG           = os.getenv("DEBUG", "false").lower() == "true"
    PORT            = int(os.getenv("PORT", 5001))

    # Lead scoring weights (tunable without code change)
    LEAD_SCORE_WEIGHTS = {
        "lead_source":   {"Referral": 20, "Inbound Call": 18, "Event": 15,
                          "Website": 12, "LinkedIn": 10, "Marketing": 8, "Cold Outreach": 5},
        "company_size":  {"1000+": 20, "201–1000": 16, "51–200": 12, "11–50": 8, "1–10": 4},
        "industry":      {"Technology": 15, "Finance": 14, "Healthcare": 12,
                          "Manufacturing": 10, "Retail": 8, "Government": 6, "Other": 5},
        "job_title_tier":{"C-Suite": 20, "VP": 16, "Director": 12, "Manager": 8, "Other": 4},
        "deal_value":    {"threshold_high": 100_000, "score_high": 15,
                          "threshold_mid": 25_000,  "score_mid": 8,
                          "score_low": 3},
    }

    VALID_LEAD_SOURCES = list(LEAD_SCORE_WEIGHTS["lead_source"].keys())
    VALID_STAGES = [
        "New Lead", "Qualified", "Proposal Sent", "Negotiation",
        "Verbal Commit", "Closed Won", "Closed Lost", "On Hold",
    ]
    VALID_ACTIVITY_TYPES = [
        "Email Sent", "Email Received", "Call", "Meeting",
        "Demo", "Proposal", "LinkedIn", "Note", "Task", "Stage Change",
    ]
    VALID_OUTCOMES = ["Positive", "Neutral", "Negative", "No Response"]
