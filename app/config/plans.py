# app/config/plans.py

from math import inf

PLAN_CONFIG = {
    # Guest: free, ad-supported, limited storage & minutes
    "guest": {
        "minutes_limit": 60,           # 60 min/month
        "features": [
            "transcribe",              # basic transcription
            "ad_supported",
            "save_3_transcripts",
            "basic_summary",
            "community_access"
        ],
    },
    # Pro: paid monthly, larger quota, ad-free
    "pro": {
        "minutes_limit": 1000,         # 1000 min/month
        "features": [
            "transcribe",
            "ad_free",
            "unlimited_storage",
            "advanced_summary",
            "priority_support"
        ],
    },
    # Premium: top-tier individual plan
    "premium": {
        "minutes_limit": inf,          # unlimited
        "features": [
            "transcribe",
            "faster_enhancements",
            "audio_export",
            "usage_analytics",
            "early_access"
        ],
    },
    # Education: discounted for schools
    "edu": {
        "minutes_limit": 500,          # 500 min/month
        "features": [
            "transcribe",
            "note_formatting",
            "group_projects",
            "educational_license",
            "faster_turnaround"
        ],
    },
    # Enterprise: for organizations
    "enterprise": {
        "minutes_limit": inf,          # unlimited
        "features": [
            "transcribe",
            "team_collaboration",
            "dedicated_onboarding",
            "private_cloud",
            "priority_api"
        ],
    },
}
