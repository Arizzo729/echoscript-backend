# app/routes/health.py
from __future__ import annotations

from datetime import datetime

import stripe
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.utils.redis_client import redis_client
from app.core.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
def health_check(db: Session = Depends(get_db)):
    """
    Performs a health check on the application and its connected services.
    
    Returns a status report for:
    - Database connectivity
    - Redis connectivity
    - Stripe API connectivity and configuration
    """
    checks = {}

    # --- Database Check ---
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e.__class__.__name__}"

    # --- Redis Check ---
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e.__class__.__name__}"

    # --- Stripe Check ---
    try:
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not set")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Account.retrieve() # A simple API call to check connectivity
        checks["stripe_api"] = "ok"
    except Exception as e:
        checks["stripe_api"] = f"error: {e.__class__.__name__}"
    
    checks["stripe_webhook_secret_present"] = bool(settings.STRIPE_WEBHOOK_SECRET)
    checks["stripe_pro_price_present"] = bool(settings.STRIPE_PRICE_PRO)
    checks["stripe_premium_price_present"] = bool(settings.STRIPE_PRICE_PREMIUM)

    # --- Determine Overall Status ---
    is_ok = all(val == "ok" for key, val in checks.items() if key.endswith("_api") or key == "database" or key == "redis")
    status = "ok" if is_ok else "degraded"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }