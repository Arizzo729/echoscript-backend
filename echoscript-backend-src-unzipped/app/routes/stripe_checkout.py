# app/routes/stripe_checkout.py
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.settings import settings
from app.dependencies import get_current_active_user
from app.models import User

router = APIRouter(prefix="/stripe-checkout", tags=["Stripe"])

class CheckoutRequest(BaseModel):
    price_id: str
    quantity: int = 1
    metadata: Optional[Dict[str, Any]] = None

@router.post("/create")
def create_checkout_session(body: CheckoutRequest, current_user: User = Depends(get_current_active_user)):
    """
    Creates a Stripe Checkout session for a user to purchase a subscription.

    - Requires an authenticated user.
    - The user's ID is passed in the session's metadata to be used in webhooks.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured on the server.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": body.price_id, "quantity": body.quantity}],
            success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.STRIPE_CANCEL_URL,
            allow_promotion_codes=True,
            # Pass the user ID in metadata to link the Stripe customer to our user
            metadata={"user_id": current_user.id, **(body.metadata or {})},
            # Pre-fill the customer email
            customer_email=current_user.email,
        )
        return {"url": session.url, "id": session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}")
def get_checkout_session(session_id: str):
    """
    Retrieves a Stripe Checkout session to check its status.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured on the server.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id, expand=["line_items", "customer"])
        return {
            "id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "customer_email": session.customer_details.email,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))