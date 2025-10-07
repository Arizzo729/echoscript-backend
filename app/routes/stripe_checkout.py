# app/routes/stripe_checkout.py

import os
import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")
if not STRIPE_SECRET:
    # let the route raise later with a friendly message
    pass

stripe.api_key = STRIPE_SECRET

router = APIRouter(prefix="/api/stripe/checkout", tags=["stripe"])

class CreateBody(BaseModel):
    mode: str | None = "subscription"  # "subscription" or "payment"
    price_id: str | None = None        # override env price
    quantity: int | None = 1

@router.post("/create")
def create_checkout_session(body: CreateBody):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on server.")
    mode = body.mode or "subscription"
    price_id = body.price_id or os.getenv("STRIPE_PRICE_PRO")
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe price id is missing. Set STRIPE_PRICE_PRO or pass price_id.")

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": body.quantity or 1}],
            success_url=(os.getenv("STRIPE_SUCCESS_URL") or "https://echoscript.ai/checkout?success=1")
                         + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("STRIPE_CANCEL_URL") or "https://echoscript.ai/checkout?canceled=1",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session")
def get_session(session_id: str):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on server.")
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["line_items", "customer", "subscription"]
        )
        return {"id": session.id, "status": session.status, "payment_status": session.payment_status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

