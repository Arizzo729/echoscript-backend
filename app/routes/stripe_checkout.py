# app/routes/stripe_checkout.py
import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/stripe", tags=["Stripe"])

# Accept either STRIPE_SECRET_KEY or STRIPE_SECRET
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")
if not STRIPE_SECRET:
    # We fail fast so your client sees a clean 400 instead of a stacktrace
    raise RuntimeError("Missing STRIPE_SECRET_KEY (or STRIPE_SECRET) in environment")

stripe.api_key = STRIPE_SECRET

SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL") or "http://localhost:5173/checkout/success"
CANCEL_URL = os.getenv("STRIPE_CANCEL_URL") or "http://localhost:5173/checkout/cancel"
PRICE_PRO   = os.getenv("STRIPE_PRICE_PRO")       # e.g. price_123
PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM") # optional

class CreateSessionBody(BaseModel):
    price_id: str | None = None          # override which price to use
    quantity: int | None = 1
    mode: str | None = "subscription"    # or "payment"
    metadata: dict | None = None

@router.post("/create-checkout-session")
def create_checkout_session(body: CreateSessionBody):
    price_id = body.price_id or PRICE_PRO
    if not price_id:
        raise HTTPException(status_code=400, detail="No price_id provided and STRIPE_PRICE_PRO not set")

    try:
        session = stripe.checkout.Session.create(
            mode=body.mode or "subscription",
            line_items=[{"price": price_id, "quantity": body.quantity or 1}],
            success_url=f"{SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=CANCEL_URL,
            allow_promotion_codes=True,
            metadata=body.metadata or {},
            automatic_tax={"enabled": True},
        )
        return {"url": session.url}
    except Exception as e:
        # The most common here is: No API key provided
        raise HTTPException(status_code=400, detail=str(e))

class PortalBody(BaseModel):
    session_id: str

@router.post("/portal")
def billing_portal(body: PortalBody, request: Request):
    """
    Create a Billing Portal session. Pass the Checkout session_id from success page.
    """
    try:
        checkout = stripe.checkout.Session.retrieve(body.session_id)
        if not checkout.get("customer"):
            raise HTTPException(status_code=400, detail="No customer on session")
        portal = stripe.billing_portal.Session.create(
            customer=checkout["customer"],
            return_url=SUCCESS_URL,
        )
        return {"url": portal.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
