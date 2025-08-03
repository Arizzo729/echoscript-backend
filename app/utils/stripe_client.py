# app/utils/stripe_client.py

from datetime import datetime
from typing import Any, Dict, Optional, cast

import stripe  # stripe’s runtime API
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import config
from app.db import SessionLocal
from app.models import Subscription, SubscriptionStatus

# Initialize Stripe with your secret key
stripe.api_key = config.STRIPE_SECRET_KEY


def create_stripe_checkout_session(
    user_id: str,
    price_id: str,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> str:
    """
    Create a Stripe Checkout Session for a subscription purchase.
    """
    try:
        customer = stripe.Customer.create(metadata={"user_id": str(user_id)})
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=(
                success_url
                or f"{config.FRONTEND_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=cancel_url or f"{config.FRONTEND_URL}/subscription/cancel",
            metadata={"user_id": str(user_id)},
        )
        # cast away Optional in the stub
        return cast(str, session.url)  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating Stripe Checkout session: {e}",
        )


def cancel_stripe_subscription(stripe_subscription_id: str) -> stripe.Subscription:
    """
    Cancel an active Stripe subscription immediately.
    """
    try:
        # the stub may not match the runtime signature here
        return stripe.Subscription.delete(stripe_subscription_id)  # type: ignore
    except Exception as e:
        # Catch any Stripe exception (e.g. invalid ID, permission error, etc.)
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error cancelling subscription: {msg}",
        )


def sync_subscription_from_stripe(event: Dict[str, Any]) -> None:
    """
    Sync subscription status in the database based on a Stripe webhook event.
    """
    obj = event.get("data", {}).get("object", {})
    metadata = obj.get("metadata", {})
    user_id = int(metadata.get("user_id", 0))

    if not user_id:
        return

    db: Session = SessionLocal()
    try:
        sub = (
            db.query(Subscription)
            .filter_by(stripe_subscription_id=obj.get("id"))
            .one_or_none()
        )

        status_value = obj.get("status")
        items = obj.get("items", {}).get("data", [])
        plan_name = items[0].get("price", {}).get("id") if items else "unknown"
        stripe_cust = obj.get("customer")
        started_at = datetime.fromtimestamp(obj.get("start_date", 0))
        current_period_end = datetime.fromtimestamp(obj.get("current_period_end", 0))

        if sub:
            sub.status = SubscriptionStatus(status_value)  # type: ignore
            sub.renewed_at = current_period_end  # type: ignore
            if status_value in {
                SubscriptionStatus.canceled.value,
                SubscriptionStatus.unpaid.value,
            }:
                sub.canceled_at = datetime.utcnow()  # type: ignore
        else:
            sub = Subscription(
                user_id=user_id,
                stripe_subscription_id=obj.get("id"),
                stripe_customer_id=stripe_cust,
                plan_name=plan_name,
                status=SubscriptionStatus(status_value),
                started_at=started_at,
                renewed_at=current_period_end,
            )
            db.add(sub)

        db.commit()
    finally:
        db.close()
