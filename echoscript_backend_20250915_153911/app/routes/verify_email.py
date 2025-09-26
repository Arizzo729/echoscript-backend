# app/routes/verify_email.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.auth import Token
from app.utils.auth_utils import create_access_token
from app.utils.db_utils import get_user_by_email
from app.utils.redis_client import delete_key, get_value  # type: ignore[attr-defined]

router = APIRouter(prefix="/verify-email", tags=["Auth"])


class VerifyEmailRequest(BaseModel):
    """
    Request schema for verifying a user's email address.
    """

    email: EmailStr = Field(..., description="Email address of the user")
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit verification code sent via email",
    )


@router.post(
    "/",
    response_model=Token,
    summary="Verify user's email with a code and activate account",
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> Token:
    """
    Verify the provided code for the user's email, mark the user as active, and return a JWT.
    """
    key = f"verify:{payload.email}"
    stored = get_value(key)
    if not stored or stored != payload.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Activate the user
    user.is_active = True  # type: ignore[assignment]
    db.commit()
    delete_key(key)

    # Issue access token
    access_token = create_access_token({"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token="",  # no refresh-token support yet
        token_type="bearer",
    )


__all__ = ["verify_email"]
