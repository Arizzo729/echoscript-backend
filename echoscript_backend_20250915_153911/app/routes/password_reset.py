import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.utils.auth_utils import hash_password
from app.utils.db_utils import get_user_by_email, update_user_password
from app.utils.logger import logger
from app.utils.redis_client import get_redis  # type: ignore[attr-defined]
from app.utils.redis_client import delete_key, get_value  # type: ignore[attr-defined]
from app.utils.send_email import send_email

router = APIRouter(prefix="/password-reset", tags=["Auth"])


class PasswordResetRequest(BaseModel):
    """
    Request schema for initiating a password reset (sends a reset code via email).
    """

    email: EmailStr = Field(
        ..., description="Email address of the user requesting a reset"
    )


class PasswordResetVerifyRequest(BaseModel):
    """
    Request schema for completing a password reset with code verification.
    """

    email: EmailStr = Field(..., description="Email address of the user")
    code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit reset code sent via email"
    )
    new_password: str = Field(..., min_length=8, description="The new password to set")


class PasswordResetResponse(BaseModel):
    """
    Generic response schema for password reset operations.
    """

    status: str = Field(..., description="Operation status, e.g. 'sent', 'ok'")


@router.post(
    "/request",
    response_model=PasswordResetResponse,
    summary="Send a password reset code to the user's email",
)
async def request_password_reset(
    req: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    # Validate user exists
    user = get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate secure 6-digit code
    code = f"{secrets.randbelow(10**6):06d}"

    # Store in Redis with 10-minute TTL
    redis_client = get_redis()
    try:
        redis_client.setex(f"pwdreset:{req.email}", 600, code)
    except Exception as e:
        logger.error(f"Could not store reset code in Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating reset code",
        )

    # Send email
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
        logger.error(f"Failed to send reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send reset email",
        )

    return PasswordResetResponse(status="sent")


@router.post(
    "/verify",
    response_model=PasswordResetResponse,
    summary="Verify reset code and update the user's password",
)
async def verify_password_reset(
    req: PasswordResetVerifyRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    # Retrieve and validate code
    try:
        stored = get_value(f"pwdreset:{req.email}")
    except Exception as e:
        logger.error(f"Error accessing Redis for code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error verifying code",
        )

    if stored is None or stored != req.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    # Update password
    hashed = hash_password(req.new_password)
    try:
        success = update_user_password(db, req.email, hashed)
    except Exception as e:
        logger.error(f"Database error updating password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    # Cleanup Redis key
    try:
        delete_key(f"pwdreset:{req.email}")
    except Exception as e:
        logger.warning(f"Failed to delete reset code from Redis: {e}")

    return PasswordResetResponse(status="ok")


__all__ = ["request_password_reset", "verify_password_reset"]
