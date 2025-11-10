import os
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")
stripe.api_key = STRIPE_SECRET or ""

router = APIRouter(prefix="/api/stripe/checkout", tags=["stripe"])

class CheckoutBody(BaseModel):
    plan: Optional[str] = None            # "pro" | "premium" | "edu"
    price_id: Optional[str] = None        # explicit price ID alternative
    mode: Optional[str] = None            # "subscription" | "payment"
    quantity: Optional[int] = 1
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.options("/create")
def preflight():
    return {}

@router.post("/create")
def create_checkout_session(body: CheckoutBody):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on server.")

    price_id = body.price_id
    if not price_id and body.plan:
        env_key = {
            "pro": "STRIPE_PRICE_PRO",
            "premium": "STRIPE_PRICE_PREMIUM",
            "edu": "STRIPE_PRICE_EDU",
        }.get(body.plan.lower().strip())
        if env_key:
            price_id = os.getenv(env_key)
    if not price_id:
        price_id = os.getenv("STRIPE_PRICE_PRO")
    if not price_id:
        raise HTTPException(status_code=400, detail="Missing price. Provide price_id or set STRIPE_PRICE_* envs.")

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
            payment_method_types=["card"],   # ✅ card only
            locale="en",                     # ✅ no dynamic './en' module
            ui_mode="hosted",                # ✅ explicit
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            metadata=body.metadata or {},
            automatic_tax={"enabled": True},
        )
        return {"url": session.url, "id": session.id}
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
