# app/routes/stripe_checkout.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import stripe

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRICE_PRO"),
    "premium": os.getenv("STRIPE_PRICE_PREMIUM"),
    "edu": os.getenv("STRIPE_PRICE_EDU"),
}

SUCCESS_URL = os.getenv(
    "STRIPE_SUCCESS_URL",
    "https://echoscript.ai/success?session_id={CHECKOUT_SESSION_ID}",
)
CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://echoscript.ai/purchase")
MODE = os.getenv("STRIPE_MODE", "subscription")

class CheckoutIn(BaseModel):
    plan: str

@router.get("/_debug-env")
def debug_env():
    return {
        "ok": True,
        "mode_default": MODE,
        "has_secret": bool(stripe.api_key),
        "price_pro": bool(PRICE_MAP.get("pro")),
        "price_premium": bool(PRICE_MAP.get("premium")),
        "price_edu": bool(PRICE_MAP.get("edu")),
        "success_url": SUCCESS_URL,
        "cancel_url": CANCEL_URL,
        "frontend": "https://echoscript.ai",
    }

@router.post("/create-checkout-session")
def create_checkout_session(data: CheckoutIn):
    price_id = PRICE_MAP.get(data.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Unknown plan")

    try:
        session = stripe.checkout.Session.create(
            mode=MODE,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            automatic_tax={"enabled": True},
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e))

