# app/models/usage_log.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base  # import Base from app/models/__init__.py

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(
                   String,
                   ForeignKey("users.id", ondelete="CASCADE"),
                   nullable=False,
                   index=True
               )
    minutes    = Column(Float, nullable=False)
    created_at = Column(
                   DateTime(timezone=True),
                   server_default=func.now(),
                   nullable=False
               )

    # back-reference to User. Make sure User.subscription_logs or usage_logs matches this.
    user       = relationship("User", back_populates="usage_logs")
