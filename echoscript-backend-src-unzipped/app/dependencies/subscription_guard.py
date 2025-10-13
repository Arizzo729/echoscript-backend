# app/dependencies/subscription_guard.py
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models import Subscription, SubscriptionStatus, User

# Define the set of statuses that are considered "active"
ALLOWED_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}

def require_active_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    FastAPI dependency that checks if the current user has an active subscription.

    - Fetches the user's most recent subscription from the database.
    - If no subscription is found, or if its status is not in ALLOWED_STATUSES,
      it raises an HTTP 402 Payment Required error.
    """
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id) # Correctly access user.id
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if not subscription or subscription.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="An active subscription is required to access this resource.",
        )