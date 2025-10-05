# app/routes/stripe_checkout.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import stripe

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET")

# env: map plans to Stripe Price IDs
PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRICE_PRO", ""),
    "premium": os.getenv("STRIPE_PRICE_PREMIUM", ""),
    "edu": os.getenv("STRIPE_PRICE_EDU", ""),
}

APP_URL = os.getenv("PUBLIC_APP_URL", "https://echoscript.ai").rstrip("/")

class CreateSessionBody(BaseModel):
    plan: str

@router.post("/api/stripe/create-checkout-session")
def create_checkout_session(body: CreateSessionBody):
    price_id = PRICE_MAP.get(body.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{body.plan}' or PRICE not set")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{APP_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/purchase?canceled=1",
            allow_promotion_codes=True,
            automatic_tax={"enabled": True},

            # 👇 keep it simple: only show card to avoid wallet modules (Amazon/Klarna/CashApp)
            payment_method_types=["card"],

            # (optional) locale hints to avoid locale module warnings
            locale="auto",
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        # bubble up a readable error for the client
        msg = getattr(e, "user_message", str(e))
        raise HTTPException(status_code=400, detail=msg)
