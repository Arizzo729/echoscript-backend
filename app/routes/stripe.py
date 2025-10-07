import os
import logging
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("stripe")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")
if not STRIPE_SECRET_KEY:
    log.warning("Stripe is not configured: STRIPE_SECRET_KEY is empty.")
stripe.api_key = STRIPE_SECRET_KEY or ""

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

@router.get("/_debug-env")
def stripe_debug_env():
    key = os.getenv("STRIPE_SECRET_KEY") or ""
    return {"has_key": bool(key), "len": len(key), "prefix": key[:6]}

@router.get("/_debug-prices")
def stripe_debug_prices():
    return {
        "pro": os.getenv("STRIPE_PRICE_PRO"),
        "premium": os.getenv("STRIPE_PRICE_PREMIUM"),
        "edu": os.getenv("STRIPE_PRICE_EDU"),
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
        env_key = {
            "pro": "STRIPE_PRICE_PRO",
            "premium": "STRIPE_PRICE_PREMIUM",
            "edu": "STRIPE_PRICE_EDU",
        }.get(plan)
        if env_key:
            price_id = os.getenv(env_key)

    if not price_id:
        raise HTTPException(status_code=400, detail="Missing price. Provide price_id or valid plan (pro|premium|edu).")

    mode = (body.mode or os.getenv("STRIPE_MODE") or "subscription").lower()
    if mode not in {"subscription", "payment"}:
        mode = "subscription"

    frontend = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    success_url = body.success_url or os.getenv("STRIPE_SUCCESS_URL") or f"{frontend}/thank-you"
    cancel_url  = body.cancel_url  or os.getenv("STRIPE_CANCEL_URL")  or f"{frontend}/purchase"
    if not success_url or not cancel_url:
        raise HTTPException(status_code=500, detail="Missing STRIPE_SUCCESS_URL/STRIPE_CANCEL_URL or FRONTEND_URL.")

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": int(body.quantity or 1)}],
            # ✅ quiet 3rd-party noise: card-only + fixed locale + hosted UI
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

