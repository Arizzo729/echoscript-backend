# app/routes/auth.py

import logging
from datetime import timedelta
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.utils.auth_utils import (create_access_token, decode_access_token,
                                  verify_password)
from app.utils.db_utils import get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["Auth"])
logger = logging.getLogger("echoscript.auth")

# Token lifetimes
ACCESS_TOKEN_EXPIRE_HOURS = 8
REFRESH_TOKEN_EXPIRE_DAYS = 7


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and issue access & refresh tokens",
)
async def login(
    creds: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """
    Validate credentials and return JWT tokens.
    """
    user = get_user_by_email(db, creds.email)
    # user.password comes in as Column[str]; cast to str for verify_password
    if not user or not verify_password(creds.password, cast(str, user.password)):
        logger.warning(f"Failed login attempt for '{creds.email}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    )
    refresh_token = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Exchange a valid refresh token for new tokens",
)
async def refresh_token(
    req: RefreshRequest,
    db: Session = Depends(get_db),
) -> Token:
    """
    Decode and validate the refresh token, then issue fresh tokens.
    """
    token = req.refresh_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "refresh" or "sub" not in payload:
        logger.warning("Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        logger.error(f"Refresh for inactive or non‑existent user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not active",
        )

    new_access = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    )
    new_refresh = create_access_token(
        data={"sub": str(user_id), "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
    )
