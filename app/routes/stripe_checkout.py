import os
import json
import logging
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("stripe_checkout")

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

def _create_extra_minutes_checkout(body: CheckoutBody, success_url: str, cancel_url: str):
    """
    Handle checkout for extra minutes bundles from the cart.
    Creates a Stripe Checkout session with custom amount from bundle items.
    """
    try:
        # Parse items from metadata
        items_json = body.metadata.get("items")
        if not items_json:
            raise HTTPException(status_code=400, detail="No items in cart")
        
        items = json.loads(items_json) if isinstance(items_json, str) else items_json
        if not items or not isinstance(items, list):
            raise HTTPException(status_code=400, detail="Invalid items format")
        
        # Calculate total amount in cents and collect item details
        total_cents = 0
        total_minutes = 0
        for item in items:
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 0))
            minutes = int(item.get("minutes", 0))
            total_cents += int(price * quantity * 100)  # Convert to cents
            total_minutes += minutes * quantity
        
        if total_cents <= 0:
            raise HTTPException(status_code=400, detail="Invalid cart total")
        
        # Create a dynamic product and price for this specific bundle
        # or use a fixed "extra minutes" product
        try:
            # Try to get or create a fixed product for extra minutes
            products = stripe.Product.list(lookup_keys=["extra_minutes"], limit=1)
            if products.data:
                product_id = products.data[0].id
            else:
                product = stripe.Product.create(
                    name="Extra Minutes",
                    description="Additional transcription minutes",
                    type="service",
                    lookup_key="extra_minutes",
                )
                product_id = product.id
        except Exception as e:
            log.warning("Could not create product, using inline pricing: %s", e)
            product_id = None
        
        # Create line item with the calculated amount
        line_items = [{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Extra {total_minutes} Minutes",
                    "description": f"Purchase {total_minutes} additional transcription minutes",
                    "images": [],
                },
                "unit_amount": total_cents,
            },
            "quantity": 1,
        }]
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            payment_method_types=["card"],
            locale="en",
            ui_mode="hosted",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            metadata={
                "type": "extra_minutes",
                "items": items_json if isinstance(items_json, str) else json.dumps(items),
                "is_gift": body.metadata.get("is_gift", False),
                "recipient_email": body.metadata.get("recipient_email", ""),
                "total_minutes": total_minutes,
            },
            automatic_tax={"enabled": True},
        )
        
        log.info("Created checkout session for extra minutes: %s", session.id)
        return {"url": session.url, "id": session.id}
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to create extra minutes checkout session")
        raise HTTPException(status_code=400, detail=f"Checkout creation failed: {str(e)}")

@router.options("/create")
def preflight():
    return {}

@router.post("/create")
def create_checkout_session(body: CheckoutBody):
    if not STRIPE_SECRET:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on server.")

    frontend = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    success_url = body.success_url or os.getenv("STRIPE_SUCCESS_URL") or f"{frontend}/thank-you"
    cancel_url = body.cancel_url or os.getenv("STRIPE_CANCEL_URL") or f"{frontend}/purchase"
    if not success_url or not cancel_url:
        raise HTTPException(status_code=500, detail="Missing STRIPE_SUCCESS_URL/STRIPE_CANCEL_URL or FRONTEND_URL.")

    try:
        # Handle extra_minutes purchase (cart checkout)
        if body.metadata and body.metadata.get("type") == "extra_minutes":
            return _create_extra_minutes_checkout(
                body, success_url, cancel_url
            )
        
        # Handle standard plan checkout
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
        return {"url": session.url, "id": session.id}
    except Exception as e:
        log.exception("Stripe session create failed")
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
