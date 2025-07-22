"""
EchoScript.AI backend application package

This file exposes top-level imports for convenient access throughout the codebase.
"""

# Configuration
from .config import config
# Database
from .db import Base, SessionLocal, engine, get_db
# Authentication dependencies
from .dependencies import get_admin_user, get_current_user, oauth2_scheme
# Models
from .models import Subscription, SubscriptionStatus, User

__all__ = [
    # Config
    "config",
    # Database
    "engine",
    "SessionLocal",
    "get_db",
    "Base",
    # Auth dependencies
    "oauth2_scheme",
    "get_current_user",
    "get_admin_user",
    # Models
    "User",
    "Subscription",
    "SubscriptionStatus",
]
