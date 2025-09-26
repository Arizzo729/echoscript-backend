# app/routes/password_reset_request.py

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.utils.db_utils import get_user_by_email
from app.utils.logger import logger
from app.utils.redis_client import get_redis  # type: ignore[attr-defined]
from app.utils.send_email import send_email

router = APIRouter(prefix="/password-reset", tags=["Auth"])


class PasswordResetRequest(BaseModel):
    """
    Request schema for initiating a password reset (sends a reset code via email).
    """

    email: EmailStr = Field(
        ..., description="Email address of the user requesting a password reset"
    )


class PasswordResetResponse(BaseModel):
    """
    Generic response schema for password reset operations.
    """

    status: str = Field(..., description="Operation status, e.g. 'sent'")


@router.post(
    "/request",
    response_model=PasswordResetResponse,
    summary="Send a password reset code to the user's email",
)
async def send_reset_code(
    req: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    # 1) Verify that the user exists in the database
    user = get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 2) Generate a secure 6‑digit code using the `secrets` module
    code = f"{secrets.randbelow(10**6):06d}"

    # 3) Store the code in Redis with a 10‑minute expiration
    redis_client = get_redis()
    try:
        redis_client.setex(f"pwdreset:{req.email}", 600, code)
    except Exception as e:
        logger.error(f"Error writing reset code to Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating reset code",
        )

    # 4) Email the code to the user
    try:
        send_email(
            to_address=req.email,
            subject="Your EchoScript.AI Password Reset Code",
            body=(
                f"Your password reset code is: {code}\n"
                "This code will expire in 10 minutes."
            ),
        )
    except Exception as e:
        logger.error(f"Error sending reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send reset email",
        )

    # 5) Return a simple acknowledgement
    return PasswordResetResponse(status="sent")


__all__ = ["send_reset_code"]
