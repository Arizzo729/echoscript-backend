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
    hashed_password = Column(String, nullable=True)  # Legacy column, may be null
    username = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    plan = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    avatar_uploaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="Subscription.user_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"


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


class Transcript(Base):
    """
    A transcript created by a user from audio/video file.
    """

    __tablename__ = "transcripts"
    __table_args__ = (Index("ix_transcripts_user_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    storage_filename = Column(String(500), nullable=False)
    content = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Transcript id={self.id!r} user_id={self.user_id!r} "
            f"title={self.title!r} status={self.status!r}>"
        )
