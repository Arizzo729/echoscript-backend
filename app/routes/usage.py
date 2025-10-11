# app/routes/usage.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter

# Mounted by main.py at /api and /v1, so these become:
#   /api/usage/summary    and   /api/usage/users
router = APIRouter(prefix="/usage", tags=["usage"])

def _period_bounds(now: datetime):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # next month start
    end = (start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, end

@router.get("/summary")
def usage_summary():
    now = datetime.now(timezone.utc)
    start, end = _period_bounds(now)
    # TODO: replace with real DB totals
    minutes_used = 0
    minutes_limit = 60
    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "minutes_used": minutes_used,
        "minutes_limit": minutes_limit,
        "minutes_remaining": max(minutes_limit - minutes_used, 0),
    }

@router.get("/users")
def users_usage():
    # TODO: return real per-user rows; shape kept generic for now
    return {
        "users": [
            # {"user_id": "example", "email": "example@example.com", "minutes_used": 0}
        ]
    }
