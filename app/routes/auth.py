# app/routes/auth.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
import traceback

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ---- import DB + models + helpers (with fallbacks) ----
_db_ok = True
try:
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError, ProgrammingError
    from sqlalchemy import LargeBinary, String

    from app.db import get_db, Base, engine  # your project DB bits
    # register models with SQLAlchemy metadata
    import app.models  # noqa: F401
    from app.models import User  # type: ignore

    try:
        from app.utils.auth_utils import hash_password, verify_password, create_access_token
    except Exception:
        # Fallbacks only to unblock; adjust to your real implementation if present
        import hashlib

        def hash_password(p: str) -> str:
            return hashlib.sha256(p.encode("utf-8")).hexdigest()

        def verify_password(p: str, hashed: str) -> bool:
            return hash_password(p) == hashed

        def create_access_token(payload: dict) -> str:
            return secrets.token_urlsafe(32)

except Exception as e:
    _db_ok = False
    _import_error = e


# ------------- Schemas -------------
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


# ------------- Helpers -------------
def _coerce_for_password_column(value):
    """
    Make sure the password value matches the column's DB type.
    If your column is LargeBinary/BYTEA, send bytes.
    If it's String/Text/VARCHAR, send str.
    """
    try:
        col = User.__table__.c.password
        if isinstance(col.type, LargeBinary):
            # column expects bytes
            if isinstance(value, str):
                return value.encode("utf-8")
            return bytes(value)
        # else it expects text
        if isinstance(value, (bytes, bytearray, memoryview)):
            return bytes(value).decode("utf-8", "ignore")
        return str(value)
    except Exception:
        # if anything goes sideways, return as-is and let the DB error surface
        return value


# ------------- Routes -------------
@router.post("/signup", response_model=SignupOut, summary="Create a new account")
def signup(payload: SignupIn, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> SignupOut:
    if not _db_ok:
        raise HTTPException(
            status_code=500,
            detail=f"auth.import_error: {_import_error.__class__.__name__}: {_import_error}",
        )

    try:
        # Ensure tables exist (idempotent)
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        hashed = hash_password(payload.password)
        hashed = _coerce_for_password_column(hashed)

        user = User(email=payload.email, password=hashed)  # type: ignore[arg-type]
        db.add(user)
        db.commit()
        db.refresh(user)
        return SignupOut(id=user.id, email=user.email)

    except HTTPException:
        raise
    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"auth.integrity_error: {ie}")
    except ProgrammingError as pe:
        db.rollback()
        # Return the real DB message so we can see exact mismatch
        raise HTTPException(status_code=500, detail=f"auth.programming_error: {pe}")
    except Exception as e:
        db.rollback()
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

