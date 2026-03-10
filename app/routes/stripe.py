import logging
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

log = logging.getLogger("stripe")
config = get_settings()

STRIPE_SECRET_KEY = config.STRIPE_SECRET_KEY
if not STRIPE_SECRET_KEY:
    log.warning("Stripe is not configured: STRIPE_SECRET_KEY is empty.")
stripe.api_key = STRIPE_SECRET_KEY or ""

# relative prefix (no /api)
router = APIRouter(prefix="/stripe", tags=["stripe"])

@router.get("/_debug-env")
def stripe_debug_env():
    key = config.STRIPE_SECRET_KEY or ""
    return {"has_key": bool(key), "len": len(key), "prefix": key[:6]}

@router.get("/_debug-prices")
def stripe_debug_prices():
    return {
        "pro": config.STRIPE_PRICE_PRO,
        "premium": config.STRIPE_PRICE_PREMIUM,
        "edu": config.STRIPE_PRICE_EDU,
    }

class LegacyBody(BaseModel):
    plan: Optional[str] = None
    price_id: Optional[str] = None
    mode: Optional[str] = None       # "subscription" | "payment"
    quantity: Optional[int] = 1
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.options("/create-checkout-session")
def legacy_preflight():
    return {}

@router.post("/create-checkout-session")
def legacy_create_checkout_session(body: LegacyBody):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on server.")

    price_id = body.price_id
    if not price_id and body.plan:
        plan = body.plan.lower().strip()
        price_map = {
            "pro": config.STRIPE_PRICE_PRO,
            "premium": config.STRIPE_PRICE_PREMIUM,
            "edu": config.STRIPE_PRICE_EDU,
        }
        price_id = price_map.get(plan)

    if not price_id:
        raise HTTPException(status_code=400, detail="Missing price. Provide price_id or valid plan (pro|premium|edu).")

    mode_raw = (body.mode or "subscription").lower()
    if mode_raw not in {"subscription", "payment"}:
        mode_raw = "subscription"
    mode: str = mode_raw

    frontend = (config.FRONTEND_URL or "").rstrip("/")
    success_url = body.success_url or f"{frontend}/thank-you"
    cancel_url  = body.cancel_url or f"{frontend}/purchase"
    if not success_url or not cancel_url:
        raise HTTPException(status_code=500, detail="Missing FRONTEND_URL in configuration.")

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": int(body.quantity or 1)}],
            payment_method_types=["card"],
            locale="en",
            ui_mode="hosted",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            metadata=body.metadata or {},
            automatic_tax={"enabled": True},
        )
        return {"url": session.url}
    except Exception as e:
        log.exception("Stripe session create failed")
        raise HTTPException(status_code=400, detail=str(e))

