from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    stripe_subscription_id = Column(String, nullable=False)

    # Use string name to avoid circular import
    user = relationship("User", back_populates="subscription")
