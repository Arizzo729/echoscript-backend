# app/utils/stripe_client.py
from __future__ import annotations

from datetime import datetime
from typing import Any

import stripe
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models import Subscription, SubscriptionStatus, User
from app.utils.logger import logger

# Initialize Stripe API key
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

def is_stripe_enabled() -> bool:
    """Returns True if the Stripe API key is configured."""
    return bool(settings.STRIPE_SECRET_KEY)

def create_stripe_checkout_session(
    user: User,
    price_id: str,
) -> stripe.checkout.Session:
    """
    Creates a Stripe Checkout Session for a user to start a subscription.
    """
    if not is_stripe_enabled():
        raise RuntimeError("Stripe is not configured.")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=settings.STRIPE_CANCEL_URL,
        customer_email=user.email,
        metadata={"user_id": user.id},
        allow_promotion_codes=True,
    )
    return session

def create_billing_portal_session(customer_id: str) -> stripe.billing_portal.Session:
    """
    Creates a Stripe Billing Portal session for a customer to manage their subscription.
    """
    if not is_stripe_enabled():
        raise RuntimeError("Stripe is not configured.")

    portal_session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.API_ALLOWED_ORIGINS.split(',')[0]}/account", # Assumes first origin is the main frontend URL
    )
    return portal_session

def sync_subscription_from_stripe_event(db: Session, event: stripe.Event) -> None:
    """
    Updates the local database with subscription data from a Stripe webhook event.
    """
    session = event.data.object
    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        logger.warning("Stripe event received without a user_id in metadata.")
        return

    subscription_id = session.get("subscription")
    customer_id = session.get("customer")

    if not subscription_id or not customer_id:
        logger.warning("Stripe event is missing subscription or customer ID.")
        return

    # Retrieve the full subscription object to get all details
    stripe_sub = stripe.Subscription.retrieve(subscription_id)

    # Find existing subscription or create a new one
    local_sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not local_sub:
        local_sub = Subscription(user_id=user_id)
        db.add(local_sub)

    # Update local subscription with data from Stripe
    local_sub.stripe_subscription_id = stripe_sub.id
    local_sub.stripe_customer_id = stripe_sub.customer
    local_sub.status = SubscriptionStatus(stripe_sub.status)
    local_sub.plan_name = stripe_sub.items.data[0].price.nickname if stripe_sub.items.data else "Unknown Plan"
    local_sub.started_at = datetime.fromtimestamp(stripe_sub.start_date)
    local_sub.updated_at = datetime.utcnow()

    db.commit()
    logger.info(f"Subscription for user {user_id} synced from Stripe.")