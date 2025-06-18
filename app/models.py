# === app/models.py ===
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # UUID (Auth0 or custom ID)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)

    # Subscription Info
    plan = Column(String, default="guest")
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Usage
    minutes_used = Column(Integer, default=0)
    minutes_limit = Column(Integer, default=60)

    # Flags
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Email or 2FA verification flag
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_email = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    plan_id = Column(String, nullable=False)
    stripe_subscription_id = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscription")


# === main.py snippet (ensure db + models are initialized) ===
from fastapi import FastAPI, Request
from app.db import engine
from app.models import Base
import stripe
import os

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS, routes, middlewares, and other imports here

# === Stripe Webhook Route ===
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return {"error": "Invalid payload"}
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}

    # Stripe event handling logic
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "customer.subscription.updated" or event_type == "customer.subscription.created":
        # Update or create subscription in DB
        stripe_subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")
        plan_id = data["items"]["data"][0]["price"]["id"]

        from app.db import get_db
        from sqlalchemy.orm import Session
        from app.models import User, Subscription

        db: Session = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
            if not sub:
                sub = Subscription(user_id=user.id, plan_id=plan_id, stripe_subscription_id=stripe_subscription_id)
                db.add(sub)
            else:
                sub.plan_id = plan_id
                sub.stripe_subscription_id = stripe_subscription_id
                sub.status = status
            db.commit()

    elif event_type == "customer.subscription.deleted":
        stripe_subscription_id = data.get("id")
        customer_id = data.get("customer")
        from app.db import get_db
        from sqlalchemy.orm import Session
        from app.models import Subscription, User

        db: Session = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
            if sub:
                sub.status = "canceled"
                db.commit()

    print("Received event:", event_type)
    return {"status": "success"}

