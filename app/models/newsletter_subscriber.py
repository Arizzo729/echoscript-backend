# app/models/newsletter_subscriber.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from . import Base  # import Base from app/models/__init__.py

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id                 = Column(Integer, primary_key=True, index=True)
    email              = Column(String, unique=True, nullable=False, index=True)
    confirmed          = Column(Boolean, default=False, nullable=False)
    confirmation_token = Column(String, nullable=True)
    subscribed_at      = Column(
                           DateTime(timezone=True),
                           server_default=func.now(),
                           nullable=False
                         )
