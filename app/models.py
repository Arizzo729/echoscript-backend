# === app/models.py ===

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Index,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from .db import Base

# --- Enumerations ---
class SubscriptionStatus(str, enum.Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    unpaid = "unpaid"
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"

# --- User Model ---
class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email"),)

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<User id={self.id!r} email={self.email!r} active={self.is_active!r}>"

# --- Subscription Model ---
class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_user_status", "user_id", "status"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), nullable=False)
    plan_name = Column(String(100), nullable=False)
    status = Column(
        SAEnum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.active,
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    renewed_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship(
        "User",
        back_populates="subscriptions",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<Subscription id={self.id!r} user_id={self.user_id!r} "
            f"plan={self.plan_name!r} status={self.status!r}>"
        )

# --- Example Item Model (for CRUD scaffolding) ---
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    def __repr__(self):
        return f"<Item id={self.id!r} name={self.name!r}>"

