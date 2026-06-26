import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Source QB Apps — each has its own realm/token
    QB_REALM      = os.getenv("QB_REALM", "yourcompany.quickbase.com")
    QB_TOKEN      = os.getenv("QB_TOKEN", "")  # read-only token scoped to all apps

    # Table IDs per source app
    QB_TICKETS_TABLE      = os.getenv("QB_TICKETS_TABLE", "")        # ServiceDeskAutomation
    QB_DEALS_TABLE        = os.getenv("QB_DEALS_TABLE", "")          # CRM-System
    QB_REPS_TABLE         = os.getenv("QB_REPS_TABLE", "")           # CRM-System
    QB_EMPLOYEES_TABLE    = os.getenv("QB_EMPLOYEES_TABLE", "")      # EmployeeOnboarding
    QB_OB_TASKS_TABLE     = os.getenv("QB_OB_TASKS_TABLE", "")       # EmployeeOnboarding
    QB_REQUESTS_TABLE     = os.getenv("QB_REQUESTS_TABLE", "")       # ProcurementWorkflow
    QB_BUDGETS_TABLE      = os.getenv("QB_BUDGETS_TABLE", "")        # ProcurementWorkflow
    QB_APPROVAL_HIST_TABLE= os.getenv("QB_APPROVAL_HIST_TABLE", "")  # ProcurementWorkflow
    QB_SNAPSHOTS_TABLE    = os.getenv("QB_SNAPSHOTS_TABLE", "")      # ExecutiveDashboard

    # Microsoft Dataverse
    DATAVERSE_ENV_URL     = os.getenv("DATAVERSE_ENV_URL", "https://yourorg.crm4.dynamics.com")
    GRAPH_TENANT_ID       = os.getenv("GRAPH_TENANT_ID", "")
    GRAPH_CLIENT_ID       = os.getenv("GRAPH_CLIENT_ID", "")
    GRAPH_CLIENT_SECRET   = os.getenv("GRAPH_CLIENT_SECRET", "")

    # Power Automate flows
    PA_DATAVERSE_SYNC_URL = os.getenv("PA_DATAVERSE_SYNC_URL", "")
    PA_ALERT_FLOW_URL     = os.getenv("PA_ALERT_FLOW_URL", "")
    PA_REPORT_FLOW_URL    = os.getenv("PA_REPORT_FLOW_URL", "")

    # App
    WEBHOOK_SECRET  = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG           = os.getenv("DEBUG", "false").lower() == "true"
    PORT            = int(os.getenv("PORT", 5004))

    # Domain weights (must sum to 1.0)
    DOMAIN_WEIGHTS = {
        "operational": 0.25,
        "commercial":  0.30,
        "people":      0.20,
        "finance":     0.25,
    }

    # Health score thresholds
    HEALTH_THRESHOLDS = {
        "excellent":       85,
        "good":            70,
        "needs_attention": 55,
        "at_risk":         40,
    }

    # KPI alert thresholds — (warning, critical) tuples
    KPI_THRESHOLDS = {
        "health_score":            (70, 55),
        "sla_met_rate":            (85, 70),    # % — alert if BELOW
        "active_breaches":         (1,  3),     # count — alert if AT OR ABOVE
        "win_rate":                (35, 20),    # % — alert if BELOW
        "quota_attainment":        (75, 50),    # % — alert if BELOW
        "onboarding_on_track_rate":(85, 70),   # % — alert if BELOW
        "avg_budget_util":         (85, 100),   # % — alert if AT OR ABOVE
        "pending_approvals":       (10, 25),    # count — alert if AT OR ABOVE
    }

    # Company info
    COMPANY_NAME  = os.getenv("COMPANY_NAME", "Your Company (Pty) Ltd")
    EXEC_EMAIL_TO = os.getenv("EXEC_EMAIL_TO", "executives@yourcompany.com")
