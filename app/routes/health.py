from __future__ import annotations

import os
from datetime import datetime

import stripe  # type: ignore[attr-defined]
from fastapi import APIRouter
from sqlalchemy import text

from app.db import SessionLocal

# These exist in your repo already
from app.utils.redis_client import redis_client  # ping()

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/_healthz")
def healthz():
    checks = {}

    # DB
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e.__class__.__name__}: {e}"

    # Redis
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e.__class__.__name__}: {e}"

    # Stripe config present
    try:
        key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
        if not key:
            raise RuntimeError("missing STRIPE_SECRET_KEY")
        stripe.api_key = key
        checks["stripe"] = "configured"
    except Exception as e:
        checks["stripe"] = f"error: {e.__class__.__name__}: {e}"

    checks["stripe_webhook_secret_present"] = bool(os.getenv("STRIPE_WEBHOOK_SECRET"))
    checks["success_url"] = os.getenv("STRIPE_SUCCESS_URL")
    checks["cancel_url"] = os.getenv("STRIPE_CANCEL_URL")

    status = (
        "ok"
        if all(v in ("ok", "configured", True, False, None) for v in checks.values())
        else "degraded"
    )
    return {
        "status": status,
        "time": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }
