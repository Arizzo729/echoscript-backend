from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SubscriptionStatus(str, Enum):
    """
    Possible statuses for a Stripe subscription.
    """

    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    unpaid = "unpaid"
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"


class User(Base):
    """
    User of the application (subscribers or guests).
    """

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email"),)

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r} active={self.is_active!r}>"


class Subscription(Base):
    """
    A user’s subscription, tied to a Stripe subscription object.
    """

    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_user_status", "user_id", "status"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), nullable=False)
    plan_name = Column(String(100), nullable=False)

    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.active,
        nullable=False,
    )

    started_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    renewed_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship(
        "User",
        back_populates="subscriptions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Subscription id={self.id!r} user_id={self.user_id!r} "
            f"plan={self.plan_name!r} status={self.status!r}>"
        )
