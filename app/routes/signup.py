# app/routes/signup.py

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import SignupRequest
from app.utils.auth_utils import hash_password
from app.utils.db_utils import get_user_by_email
from app.utils.logger import logger
from app.utils.redis_client import set_value  # type: ignore[attr-defined]
from app.utils.send_email import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])


class SignupResponse(BaseModel):
    """
    Response schema for user signup.
    """

    status: str = Field(..., description="Operation status, e.g. 'sent'")


@router.post(
    "/signup",
    response_model=SignupResponse,
    summary="Register a new user and send email verification code",
)
async def signup(
    req: SignupRequest,
    db: Session = Depends(get_db),
) -> SignupResponse:
    # 1) Prevent duplicate registrations
    if get_user_by_email(db, req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # 2) Create the new user (inactive)
    hashed_pw = hash_password(req.password)
    user = User(email=req.email, password=hashed_pw, is_active=False)
    db.add(user)
    db.commit()

    # 3) Generate a secure 6-digit code
    code = f"{secrets.randbelow(10**6):06d}"

    # 4) Store in Redis for 1 hour
    try:
        set_value(f"verify:{req.email}", code, ex=3600)
    except Exception as e:
        logger.error(f"Redis error while storing signup code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating verification code",
        )

    # 5) Send verification email
    try:
        send_email(
            to_address=req.email,
            subject="Welcome to EchoScript.AI — Verify Your Email",
            body=(
                f"Hello {req.email},\n\n"
                f"Thanks for signing up! Your verification code is: {code}\n"
                "It will expire in 1 hour."
            ),
        )
    except Exception as e:
        logger.error(f"Failed to send signup verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send verification email",
        )

    return SignupResponse(status="sent")
