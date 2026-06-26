import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Quickbase — Transformation Tracker app
    QB_REALM                 = os.getenv("QB_REALM", "yourcompany.quickbase.com")
    QB_TOKEN                 = os.getenv("QB_TOKEN", "")
    QB_INITIATIVES_TABLE     = os.getenv("QB_INITIATIVES_TABLE", "")
    QB_BASELINES_TABLE       = os.getenv("QB_BASELINES_TABLE", "")
    QB_MILESTONES_TABLE      = os.getenv("QB_MILESTONES_TABLE", "")
    QB_ROI_TABLE             = os.getenv("QB_ROI_TABLE", "")
    QB_ROI_MONTHLY_TABLE     = os.getenv("QB_ROI_MONTHLY_TABLE", "")
    QB_LESSONS_TABLE         = os.getenv("QB_LESSONS_TABLE", "")

    # Power Automate flows
    PA_MONTHLY_REPORT_URL    = os.getenv("PA_MONTHLY_REPORT_URL", "")
    PA_BENEFIT_ALERT_URL     = os.getenv("PA_BENEFIT_ALERT_URL", "")

    # App
    WEBHOOK_SECRET           = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
    DEBUG                    = os.getenv("DEBUG", "false").lower() == "true"
    PORT                     = int(os.getenv("PORT", 5006))

    # Organization details
    COMPANY_NAME             = os.getenv("COMPANY_NAME", "Meridian Professional Services")
    DISCOUNT_RATE            = float(os.getenv("DISCOUNT_RATE", "0.10"))
    HOURLY_RATE_ZAR          = float(os.getenv("HOURLY_RATE_ZAR", "350"))

    # Benefit realization thresholds
    REALISATION_EXCELLENT    = 100.0
    REALISATION_ON_TRACK     = 85.0
    REALISATION_AT_RISK      = 70.0
    # Below AT_RISK = Underperforming

    # Initiative data (seed — matches QB records)
    INITIATIVES = {
        "INIT-01": {
            "name":       "Service Desk Automation",
            "domain":     "Operational",
            "investment": 520_000,
            "annual_opex":  96_000,
            "projected_annual_benefit": 655_200,
        },
        "INIT-02": {
            "name":       "CRM & Sales Pipeline",
            "domain":     "Commercial",
            "investment": 480_000,
            "annual_opex":  84_000,
            "projected_annual_benefit": 1_821_800,
        },
        "INIT-03": {
            "name":       "Employee Onboarding Platform",
            "domain":     "People",
            "investment": 420_000,
            "annual_opex":  72_000,
            "projected_annual_benefit": 955_425,
        },
        "INIT-04": {
            "name":       "Procurement Approval System",
            "domain":     "Finance",
            "investment": 360_000,
            "annual_opex":  84_000,
            "projected_annual_benefit": 713_400,
        },
        "INIT-05": {
            "name":       "Executive KPI Dashboard",
            "domain":     "Intelligence",
            "investment": 180_000,
            "annual_opex":  60_000,
            "projected_annual_benefit": 340_000,
        },
        "INIT-06": {
            "name":       "API Integration Hub",
            "domain":     "Integration",
            "investment": 120_000,
            "annual_opex":  48_000,
            "projected_annual_benefit": 400_750,
        },
    }

    TOTAL_INVESTMENT = sum(i["investment"] for i in INITIATIVES.values())
    TOTAL_ANNUAL_OPEX = sum(i["annual_opex"] for i in INITIATIVES.values())
    TOTAL_PROJECTED_ANNUAL_BENEFIT = sum(i["projected_annual_benefit"] for i in INITIATIVES.values())
