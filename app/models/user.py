# app/models/user.py
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class User(Base):
    __tablename__ = "users"

    id                     = Column(String, primary_key=True, index=True,
                                doc="UUID from Auth0 or equivalent")
    email                  = Column(String, unique=True, nullable=False, index=True)
    username               = Column(String, nullable=True)

    # Plan & Billing
    plan                   = Column(String, default="guest", nullable=False,
                                doc="User plan: guest, pro, enterprise")
    stripe_customer_id     = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Usage & Limits
    minutes_used           = Column(Integer, default=0, nullable=False)
    minutes_limit          = Column(Integer, default=60, nullable=False)

    # Permissions & Security
    is_active              = Column(Boolean, default=True, nullable=False)
    is_admin               = Column(Boolean, default=False, nullable=False)
    is_verified            = Column(Boolean, default=False, nullable=False)
    two_factor_enabled     = Column(Boolean, default=False, nullable=False)
    two_factor_email       = Column(String, nullable=True)

    # Timestamps
    created_at             = Column(DateTime(timezone=True),
                                   server_default=func.now(), nullable=False)
    updated_at             = Column(DateTime(timezone=True),
                                   onupdate=func.now())

    # 1:1 Subscription
    subscription           = relationship(
                                "Subscription",
                                back_populates="user",
                                uselist=False,
                                cascade="all, delete-orphan"
                             )

    # 1:N Usage logs
    usage_logs             = relationship(
                                "UsageLog",
                                back_populates="user",
                                cascade="all, delete-orphan"
                             )

    def get_minutes_used_last_30_days(self):
        from datetime import datetime, timedelta
        threshold = datetime.utcnow() - timedelta(days=30)
        return sum(
          log.minutes for log in self.usage_logs
          if log.created_at >= threshold
        )

