# app/routes/usage.py
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter

router = APIRouter(prefix="/usage", tags=["usage"])

def _month_bounds(now: datetime):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, end

@router.get("/summary")
def usage_summary():
    now = datetime.now(timezone.utc)
    start, end = _month_bounds(now)
    # TODO: replace with real DB totals per user
    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "minutes_used": 0,
        "minutes_limit": 60,
        "minutes_remaining": 60,
    }

@router.get("/users")
def users_usage():
    # TODO: return real per-user usage
    return {"users": []}
