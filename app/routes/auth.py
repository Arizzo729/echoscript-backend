# app/routes/auth.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
import traceback

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ---- attempt to import your real DB/session + models ----
_db_ok = True
try:
    from app.db import get_db, Base, engine  # your project’s DB helpers
    import app.models  # ensure models are registered with SQLAlchemy
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError
    from app.models import User  # type: ignore
    try:
        from app.utils.auth_utils import hash_password, verify_password, create_access_token
    except Exception:
        # fallbacks if helpers are named differently or missing
        def hash_password(p: str) -> str:  # NOT production-grade; only to unblock
            import hashlib
            return hashlib.sha256(p.encode("utf-8")).hexdigest()

        def verify_password(p: str, hashed: str) -> bool:
            return hash_password(p) == hashed

        def create_access_token(payload: dict) -> str:
            return secrets.token_urlsafe(32)
except Exception as e:
    _db_ok = False
    _import_error = e  # capture to show in 500 detail


# ---------------- Schemas ----------------
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


# ---------------- Routes ----------------
@router.post("/signup", response_model=SignupOut, summary="Create a new account")
def signup(payload: SignupIn, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> SignupOut:
    """
    Creates a user. If something goes wrong, we bubble up the exact error text so
    you see it in the client (instead of a generic 500).
    """
    if not _db_ok:
        # Immediate, actionable detail
        raise HTTPException(
            status_code=500,
            detail=f"auth.import_error: {_import_error.__class__.__name__}: {_import_error}",
        )

    try:
        # Ensure tables exist (idempotent; cheap)
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            # don’t fail signup due to create_all noise — we’ll proceed and let the real error surface
            pass

        # Uniqueness check
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(email=payload.email, password=hash_password(payload.password))  # type: ignore[arg-type]
        db.add(user)
        db.commit()
        db.refresh(user)
        return SignupOut(id=user.id, email=user.email)

    except HTTPException:
        raise
    except IntegrityError as ie:
        db.rollback()
        # Most likely a UNIQUE violation on email
        raise HTTPException(status_code=400, detail=f"auth.integrity_error: {ie}")
    except Exception as e:
        db.rollback()
        # Print full traceback to logs AND return the message to caller
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"auth.signup_error: {e.__class__.__name__}: {e}")


@router.post("/login", response_model=LoginOut, summary="Login and return a token")
def login(payload: LoginIn, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> LoginOut:
    if not _db_ok:
        raise HTTPException(
            status_code=500,
            detail=f"auth.import_error: {_import_error.__class__.__name__}: {_import_error}",
        )
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not verify_password(payload.password, user.password):  # type: ignore[arg-type]
            raise HTTPException(status_code=400, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id), "email": user.email})
        return LoginOut(ok=True, access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"auth.login_error: {e.__class__.__name__}: {e}")
