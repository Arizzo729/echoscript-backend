from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # UUID (Auth0 ID or similar)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)

    # Subscription Info
    plan = Column(String, default="guest")  # guest, pro, enterprise
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Usage
    minutes_used = Column(Integer, default=0)
    minutes_limit = Column(Integer, default=60)  # Guests start with 60

    # Flags
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
