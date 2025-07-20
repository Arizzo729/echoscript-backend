import stripe
from app.config import Config
from app.models import Subscription
from app.db import db_session
from datetime import datetime

stripe.api_key = Config.STRIPE_SECRET_KEY
DOMAIN = Config.FRONTEND_URL or "https://echoscript.ai"

# =====================
# CREATE CHECKOUT SESSION
# =====================
def create_stripe_checkout_session(user, price_id: str) -> str:
    try:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": user.id}
        )

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{DOMAIN}/purchase?canceled=true",
            subscription_data={
                "metadata": {"user_id": user.id},
                "trial_period_days": 0  # or change to 7 if offering trial
            },
        )

        return session.url
    except Exception as e:
        raise RuntimeError(f"Stripe checkout creation failed: {str(e)}")


# =====================
# CANCEL SUBSCRIPTION
# =====================
def cancel_stripe_subscription(stripe_subscription_id: str):
    try:
        stripe.Subscription.delete(stripe_subscription_id)
    except Exception as e:
        raise RuntimeError(f"Subscription cancellation failed: {str(e)}")


# =====================
# RETRIEVE SUBSCRIPTION
# =====================
def get_stripe_subscription(stripe_subscription_id: str):
    try:
        return stripe.Subscription.retrieve(stripe_subscription_id)
    except Exception as e:
        raise RuntimeError(f"Retrieve subscription failed: {str(e)}")


# =====================
# SYNC DB WITH STRIPE WEBHOOK
# (You’d call this from your /webhook route)
# =====================
def sync_subscription_from_stripe(event):
    try:
        if event["type"] == "customer.subscription.created" or event["type"] == "customer.subscription.updated":
            sub = event["data"]["object"]
            stripe_customer_id = sub["customer"]
            stripe_subscription_id = sub["id"]
            user_id = int(sub["metadata"].get("user_id"))

            db_sub = db_session.query(Subscription).filter_by(user_id=user_id).first()

            if not db_sub:
                db_sub = Subscription(user_id=user_id)

            db_sub.stripe_subscription_id = stripe_subscription_id
            db_sub.stripe_customer_id = stripe_customer_id
            db_sub.plan_name = sub["plan"]["nickname"] or "default"
            db_sub.status = sub["status"]
            db_sub.started_at = datetime.fromtimestamp(sub["start_date"])
            db_sub.renewed_at = datetime.fromtimestamp(sub["current_period_start"])

            db_session.add(db_sub)
            db_session.commit()
    except Exception as e:
        raise RuntimeError(f"Stripe sync failed: {str(e)}")
