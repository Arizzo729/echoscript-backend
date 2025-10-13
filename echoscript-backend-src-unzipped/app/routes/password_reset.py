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
from app.utils.redis_client import get_redis
from app.utils.send_email import send_email, EmailError
from app.core.settings import settings

router = APIRouter(prefix="/password-reset", tags=["Auth"])

TOKEN_TTL_MINUTES = 30

@router.post("/request", response_model=PasswordResetResponse)
def request_password_reset(
    payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """
    Handles a password reset request.
    
    - Finds the user by email.
    - Generates a secure, single-use token.
    - Stores the token in Redis with a TTL.
    - Sends the token to the user via email.
    - Always returns a success response to prevent email enumeration attacks.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Still return a success-like response to prevent user enumeration
        return PasswordResetResponse(sent=True)

    token = secrets.token_urlsafe(32)
    redis = get_redis()
    redis.set(f"password_reset:{token}", str(user.id), ex=TOKEN_TTL_MINUTES * 60)

    try:
        email_body = (
            f"You are receiving this email because a password reset request was made for your account.\n\n"
            f"Please use the following token to reset your password. The token is valid for {TOKEN_TTL_MINUTES} minutes.\n\n"
            f"Token: {token}\n\n"
            f"If you did not request a password reset, please ignore this email."
        )
        send_email(
            to_address=user.email,
            subject="Your Password Reset Token",
            body_text=email_body,
        )
    except EmailError as e:
        # If email fails, we can't do much, but we shouldn't expose the error.
        # Logging is handled within the send_email utility.
        pass

    return PasswordResetResponse(sent=True) # `sent` is reused for success status


@router.post("/confirm", response_model=PasswordResetResponse)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """
    Confirms a password reset using a token.

    - Validates the token from the request payload.
    - Retrieves the user ID from Redis using the token.
    - Updates the user's password with the new, hashed password.
    """
    redis = get_redis()
    user_id = redis.get(f"password_reset:{payload.token}")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        # This case should be rare if the token is valid
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.password = hash_password(payload.new_password)
    db.commit()

    # Invalidate the token after use
    redis.delete(f"password_reset:{payload.token}")

    return PasswordResetResponse(sent=True) # `sent` is reused for success status