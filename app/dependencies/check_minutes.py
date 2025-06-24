# app/dependencies/check_minutes.py

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config.plans import PLAN_CONFIG
from app.db import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.usage_log import UsageLog


def check_minutes(estimated_minutes: float):
    """
    Dependency that enforces a rolling 30-day quota of transcription minutes.
    Logs each usage event and raises HTTP 402 if the user exceeds their plan limit.

    :param estimated_minutes: Minutes to be consumed by this request.
    """
    def _check(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> bool:
        # Determine user plan and monthly limit
        plan = user.plan or "guest"
        limit = PLAN_CONFIG.get(plan, PLAN_CONFIG["guest"])["minutes_limit"]

        # Calculate usage over the past 30 days
        window_start = datetime.utcnow() - timedelta(days=30)
        used = db.query(
            func.coalesce(func.sum(UsageLog.transcript_minutes), 0.0)
        ).filter(
            UsageLog.user_id == user.id,
            UsageLog.created_at >= window_start
        ).scalar() or 0.0

        # Block if exceeding limit
        if limit != float("inf") and (used + estimated_minutes) > limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Monthly limit of {limit} minutes reached (used {used:.2f}). "
                    "Please upgrade your plan."
                )
            )

        # Log new usage event
        log = UsageLog(
            user_id=user.id,
            transcript_minutes=estimated_minutes,
            transcript_seconds=int(estimated_minutes * 60)
        )
        db.add(log)
        db.commit()

        return True

    return _check
