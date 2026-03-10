# app/routes/password_reset.py
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import (
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetResponse,
)
from app.utils.auth_utils import hash_password
from app.utils.redis_client import get_value, set_value
from app.utils.send_email import send_email

router = APIRouter(prefix="/password-reset", tags=["Password Reset"])
TOKEN_TTL_MIN = 30


@router.post("/request", response_model=PasswordResetResponse)
def request_reset(
    payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> PasswordResetResponse:
    user: User | None = db.query(User).filter(User.email == payload.email).one_or_none()
    if not user:
        return PasswordResetResponse(sent=True)

    token = secrets.token_urlsafe(32)
    set_value(f"pwreset:{token}", str(user.id), ex=TOKEN_TTL_MIN * 60)
    try:
        send_email(
            to_address=user.email,
            subject="Reset your EchoScript password",
            body=(
                f"Use this token within {TOKEN_TTL_MIN} minutes:\n\n{token}\n\n"
                "If you didn't request this, you can ignore this email."
            ),
        )
    except Exception:
        pass
    return PasswordResetResponse(sent=True)


@router.post("/confirm", response_model=PasswordResetResponse)
def confirm_reset(
    payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)
) -> PasswordResetResponse:
    uid = get_value(f"pwreset:{payload.token}")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    user: User | None = db.query(User).filter(User.id == int(uid)).one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.password = hash_password(payload.new_password)  # type: ignore[assignment]
    db.commit()
    return PasswordResetResponse(sent=True)
