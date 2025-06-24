from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.plans import PLAN_CONFIG
from app.db import get_db
from app.auth import get_current_user  # JWT/session dependency
from app.models.user import User


def ensure_feature(feature: str):
    """
    Dependency factory that ensures the current user has access to the given feature.
    Raises 403 Forbidden if not allowed.

    :param feature: Name of the feature to check
    """
    def _ensure(user: User = Depends(get_current_user)) -> bool:
        plan = user.plan or "guest"
        config = PLAN_CONFIG.get(plan, PLAN_CONFIG["guest"])
        allowed = config.get("features", [])
        if "*" not in allowed and feature not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature}' is not available on the '{plan}' plan."
            )
        return True
    return _ensure


def check_minutes(estimated: int):
    """
    Dependency factory that checks and updates the user's minutes usage.
    Raises 402 Payment Required if usage exceeds plan limit.

    :param estimated: Estimated minutes to consume
    """
    def _checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> bool:
        plan = user.plan or "guest"
        limit = PLAN_CONFIG.get(plan, PLAN_CONFIG["guest"])["minutes_limit"]  # ← fixed syntax

        if limit != float("inf") and (user.minutes_used + estimated) > limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"You have reached your monthly limit of {limit} minutes. "
                    "Please upgrade your plan to continue."
                )
            )

        # Update and persist usage
        user.minutes_used += estimated
        db.commit()
        return True

    return _checker
