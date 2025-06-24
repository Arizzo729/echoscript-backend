from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, doc="UUID from Auth0 or equivalent")
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)

    # Plan & Billing
    plan = Column(String, default="guest", nullable=False, doc="User plan: guest, pro, enterprise")
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)  # Legacy support

    # Usage & Limits
    minutes_used = Column(Integer, default=0, nullable=False)
    minutes_limit = Column(Integer, default=60, nullable=False)

    # Permissions & Security
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_email = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_id = Column(String, nullable=False, doc="Stripe Price ID")
    stripe_subscription_id = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False, doc="active, canceled, past_due, etc.")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscription")


