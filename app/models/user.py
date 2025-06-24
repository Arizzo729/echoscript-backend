from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    # Primary identification
    id = Column(String(36), primary_key=True, index=True, doc="UUID from Auth0 or similar provider")
    email = Column(String(255), unique=True, nullable=False, index=True, doc="User email address")
    username = Column(String(50), nullable=True, doc="Optional display username")

    # Subscription & plan details
    plan = Column(String(50), default="guest", nullable=False, doc="Subscription plan: guest, pro, edu, premium, enterprise")
    stripe_customer_id = Column(String(100), nullable=True, doc="Stripe customer identifier")
    stripe_subscription_id = Column(String(100), nullable=True, doc="Stripe subscription identifier")

    # Permissions & flags
    is_active = Column(Boolean, default=True, nullable=False, doc="Whether the user account is active")
    is_admin = Column(Boolean, default=False, nullable=False, doc="Admin privileges flag")

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Usage logs (one-to-many relationship)
    usage_logs = relationship(
        "UsageLog",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="List of usage log records for the last 30 days and beyond"
    )

    def get_minutes_used_last_30_days(self):
        """
        Calculate the sum of 'minutes' from usage_logs in the past 30 days.
        """
        from datetime import datetime, timedelta
        threshold = datetime.utcnow() - timedelta(days=30)
        return sum(log.minutes for log in self.usage_logs if log.created_at >= threshold)

