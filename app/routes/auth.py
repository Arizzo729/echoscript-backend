# app/routes/auth.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import secrets

from app.db import get_db
from app.models import User
from app.utils.auth_utils import hash_password
try:
    # if you have these, we’ll use them
    from app.utils.auth_utils import verify_password, create_access_token
except Exception:
    verify_password = None
    create_access_token = None

# bridge to your existing reset handlers
from app.routes.password_reset import request_reset as _pw_request_reset
from app.routes.password_reset import confirm_reset as _pw_confirm_reset

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ---------- Schemas ----------
class SignupIn(BaseModel):
    email: EmailStr
    password: str

class SignupOut(BaseModel):
    id: int
    email: EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class LoginOut(BaseModel):
    ok: bool
    access_token: str
    token_type: str = "bearer"

class ResetRequestIn(BaseModel):
    email: EmailStr

class ResetConfirmIn(BaseModel):
    email: EmailStr | None = None  # kept for compatibility
    token: str
    new_password: str

# ---------- Auth ----------
@router.post("/signup", response_model=SignupOut, summary="Create a new account")
def signup(payload: SignupIn, db: Session = Depends(get_db)) -> SignupOut:
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=payload.email, password=hash_password(payload.password))  # type: ignore[arg-type]
    db.add(user)
    db.commit()
    db.refresh(user)
    return SignupOut(id=user.id, email=user.email)

@router.post("/login", response_model=LoginOut, summary="Login and return a token")
def login(payload: LoginIn, db: Session = Depends(get_db)) -> LoginOut:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # verify password
    if verify_password:
        ok = verify_password(payload.password, user.password)  # type: ignore[arg-type]
    else:
        # fallback: compare hashed input (only if your hash_password is deterministic)
        ok = hash_password(payload.password) == user.password  # type: ignore[comparison-overlap]
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if create_access_token:
        token = create_access_token({"sub": str(user.id), "email": user.email})
    else:
        token = secrets.token_urlsafe(32)

    return LoginOut(ok=True, access_token=token)

# ---------- Password reset (aliases the existing /password-reset/*) ----------
@router.post("/send-reset-code", summary="Send password reset code (alias)")
def send_reset_code(payload: ResetRequestIn, db: Session = Depends(get_db)):
    # maps to: POST /password-reset/request
    return _pw_request_reset(payload, db=db)

@router.post("/verify-reset", summary="Verify reset token and set new password (alias)")
def verify_reset(payload: ResetConfirmIn, db: Session = Depends(get_db)):
    # maps to: POST /password-reset/confirm
    return _pw_confirm_reset(payload, db=db)
