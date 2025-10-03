# app/routes/stripe_checkout.py
import os
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# --- Stripe config from env ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_MODE = os.getenv("STRIPE_MODE", "subscription")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "") or os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM", "")
STRIPE_PRICE_EDU = os.getenv("STRIPE_PRICE_EDU", "")
SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://echoscript.ai/purchase/success?session_id={CHECKOUT_SESSION_ID}")
CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://echoscript.ai/purchase")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ---------- Debug probe (safe) ----------
@router.get("/_debug-env")
def stripe_debug_env():
    """Small, safe probe to verify wiring from the frontend through Netlify to the API."""
    return {
        "ok": True,
        "mode_default": STRIPE_MODE,
        "has_secret": bool(STRIPE_SECRET_KEY),
        "has_public": bool(STRIPE_PUBLIC_KEY),
        "price_pro?": bool(STRIPE_PRICE_PRO),
        "price_premium?": bool(STRIPE_PRICE_PREMIUM),
        "price_edu?": bool(STRIPE_PRICE_EDU),
        "success_url": SUCCESS_URL,
        "cancel_url": CANCEL_URL,
        "frontend": os.getenv("FRONTEND_URL", "https://echoscript.ai"),
    }

# ---------- Minimal checkout session ----------
class CheckoutPayload(BaseModel):
    plan: Optional[str] = "pro"  # pro | premium | edu
    mode: Optional[str] = None   # override subscription / payment

def _resolve_price(plan: str) -> str:
    plan = (plan or "pro").lower()
    if plan == "premium" and STRIPE_PRICE_PREMIUM:
        return STRIPE_PRICE_PREMIUM
    if plan == "edu" and STRIPE_PRICE_EDU:
        return STRIPE_PRICE_EDU
    if STRIPE_PRICE_PRO:
        return STRIPE_PRICE_PRO
    raise HTTPException(status_code=400, detail="No Stripe price configured for requested plan")

@router.post("/create-checkout-session")
def create_checkout_session(payload: CheckoutPayload):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    price_id = _resolve_price(payload.plan)
    mode = (payload.mode or STRIPE_MODE or "subscription").lower()

    try:
        if mode == "payment":
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=SUCCESS_URL,
                cancel_url=CANCEL_URL,
            )
        else:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=SUCCESS_URL,
                cancel_url=CANCEL_URL,
            )
        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
