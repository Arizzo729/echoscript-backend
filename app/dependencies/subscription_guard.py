# app/dependencies/subscription_guard.py
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Subscription, SubscriptionStatus

ALLOWED_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}


def require_active_subscription(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user["id"])
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if not sub or sub.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="An active subscription is required.",
        )
