from __future__ import annotations

import hashlib
from fastapi import APIRouter, Depends, Request, HTTPException, status
from jose import jwt, JWTError

from app.config import config
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User

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
def get_profile(request: Request, db: Session = Depends(get_db)):
    """Return profile for current user. Accepts Bearer token or cookie named `access_token`.
    """
    token = None
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    if not token:
        # try cookie (default cookie name used in auth routes)
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = int(sub)
    except (JWTError, ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    name = getattr(user, "name", None) or user.email.split("@")[0]

    plan = "Guest"
    try:
        subs = [s for s in getattr(user, "subscriptions", []) if getattr(s, "status", None) == "active"]
        if subs:
            plan = subs[0].plan_name or "Pro"
        else:
            allsubs = getattr(user, "subscriptions", [])
            if allsubs:
                plan = allsubs[-1].plan_name or "Pro"
    except Exception:
        plan = "Guest"

    minutes_used = 0.0
    sessions = 0
    avatar = _gravatar_url(user.email)

    return ProfileOut(
        id=user.id,
        email=user.email,
        name=name,
        plan=plan,
        minutesUsed=minutes_used,
        sessions=sessions,
        avatar=avatar,
    )
