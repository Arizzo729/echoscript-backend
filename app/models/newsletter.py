from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from database import Base

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    confirmed = Column(Boolean, default=False)
    confirmation_token = Column(String, nullable=True)
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
