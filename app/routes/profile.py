from __future__ import annotations

import hashlib
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status
from jose import jwt, JWTError

from app.config import config
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User

log = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    plan: str
    minutesUsed: float = 0
    sessions: int = 0
    avatar: str | None = None


def _gravatar_url(email: str, size: int = 160) -> str:
    h = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{h}?s={size}&d=identicon"


@router.get("/", response_model=ProfileOut)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return profile for current user.
    """
    try:
        user = current_user
        # Try to get the real name first, then username, then fallback to email prefix
        display_name = getattr(user, "name", None) or getattr(user, "username", None) or user.email.split("@")[0]
        log.info(f"Fetching profile for user {user.id}: name={display_name}, email={user.email}")

        # Determine plan name
        plan_name = "Guest"
        try:
            # Check active subscriptions
            active_subs = [s for s in getattr(user, "subscriptions", []) if getattr(s, "status", None) == "active"]
            if active_subs:
                # Use the most recent active subscription's plan name
                plan_name = active_subs[-1].plan_name or "Pro"
            else:
                # Fallback to last known subscription if any, or check for plan_name on user if exists
                all_subs = getattr(user, "subscriptions", [])
                if all_subs:
                    plan_name = all_subs[-1].plan_name or "Pro"
                elif hasattr(user, "plan_name") and user.plan_name:
                    plan_name = user.plan_name
        except Exception as e:
            log.error(f"Error determining plan for user {user.id}: {e}")
            plan_name = "Guest"

        try:
            from app.models.transcript import Transcript
            transcripts = db.query(Transcript).filter(Transcript.user_id == user.id).all()
            minutes_used = sum(((t.duration or 0) / 60) for t in transcripts)
            sessions = len(transcripts)
        except Exception as e:
            log.exception(f"Error fetching usage for profile: {e}")
            minutes_used = 0.0
            sessions = 0
        avatar = _gravatar_url(user.email)

        try:
            from app.models.user import User as DBUser
            db_user = db.query(DBUser).filter(DBUser.id == user.id).first()
            avatar_url = db_user.avatar_url if db_user else None
        except Exception as e:
            log.error(f"Error fetching avatar for user {user.id}: {e}")
            avatar_url = None
        
        return ProfileOut(
            id=user.id,
            email=user.email,
            name=display_name,
            plan=plan_name,
            minutesUsed=minutes_used,
            sessions=sessions,
            avatar=avatar_url or _gravatar_url(user.email),
        )
    except Exception as e:
        log.exception(f"Profile endpoint error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
