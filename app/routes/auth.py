# app/routes/auth.py
import logging
from datetime import timedelta
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.utils.auth_utils import create_access_token, decode_access_token, verify_password
from app.utils.db_utils import get_user_by_email

logger = logging.getLogger("echoscript")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

ACCESS_TOKEN_EXPIRE_HOURS = 12
REFRESH_TOKEN_EXPIRE_DAYS = 30


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email & password to receive access/refresh tokens",
)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = get_user_by_email(db, req.email)
    if user is None or not verify_password(req.password, cast(str, user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    )
    refresh = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return Token(access_token=access, refresh_token=refresh, token_type="bearer")


@router.post(
    "/refresh",
    response_model=Token,
    summary="Exchange a valid refresh token for new tokens",
)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    payload = decode_access_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )
    user_id = payload.get("sub")
    user: User | None = db.query(User).filter(User.id == int(user_id)).one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    new_access = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    )
    new_refresh = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return Token(
        access_token=new_access, refresh_token=new_refresh, token_type="bearer"
    )
