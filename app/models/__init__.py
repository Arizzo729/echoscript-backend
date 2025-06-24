# app/models/__init__.py
from sqlalchemy.orm import declarative_base

# single Base for all models
Base = declarative_base()

# optionally expose your models at the package level
from .user import User
from .subscription import Subscription
from .usage_log import UsageLog
from .newsletter_subscriber import NewsletterSubscriber
