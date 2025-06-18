from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # UUID (e.g., from Auth0)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)

    # Plan & Stripe Info
    plan = Column(String, default="guest")  # guest, pro, enterprise, etc.
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)  # Legacy fallback

    # Usage Tracking
    minutes_used = Column(Integer, default=0)
    minutes_limit = Column(Integer, default=60)

    # User Flags
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_email = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_id = Column(String, nullable=False)  # Stripe price ID
    stripe_subscription_id = Column(String, nullable=False)
    status = Column(String, default="active")  # active, canceled, past_due, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscription")


