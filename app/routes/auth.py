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
    from sqlalchemy import LargeBinary

    from app.db import get_db, Base, engine
    import app.models  # register models
    from app.models import User  # type: ignore

    try:
        from app.utils.auth_utils import hash_password, verify_password, create_access_token
    except Exception:
        # Simple fallbacks (not for production crypto)
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


# ---------------- Helpers ----------------
def _find_col(name_candidates):
    cols = User.__table__.c
    for n in name_candidates:
        if n in cols:
            return n, cols[n]
    return None, None

def _coerce_for_password_column(value, coltype):
    # If the DB column is BYTEA/LargeBinary, store bytes; else store text
    if isinstance(coltype, LargeBinary):
        return value.encode("utf-8") if isinstance(value, str) else bytes(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", "ignore")
    return str(value)


# ---------------- Routes ----------------
@router.post("/signup", response_model=SignupOut, summary="Create a new account")
def signup(payload: SignupIn, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> SignupOut:
    if not _db_ok:
        raise HTTPException(status_code=500, detail=f"auth.import_error: {_import_error}")

    # Determine real column names
    email_col_name, _ = _find_col(["email", "user_email", "username"])
    pass_col_name, pass_col_type = _find_col(["password", "password_hash", "hashed_password"])

    if not email_col_name or not pass_col_name:
        raise HTTPException(
            status_code=500,
            detail=f"auth.model_mismatch: Could not find expected columns on User. "
                   f"Have: {list(User.__table__.c.keys())} "
                   f"Need one of email/user_email/username and one of password/password_hash/hashed_password."
        )

    try:
        # ensure tables (idempotent)
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        # unique email check
        existing = db.query(User).filter(getattr(User, email_col_name) == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        hashed = _coerce_for_password_column(hash_password(payload.password), pass_col_type.type)

        user_kwargs = {email_col_name: payload.email, pass_col_name: hashed}
        user = User(**user_kwargs)  # type: ignore[arg-type]
        db.add(user)
        db.commit()
        db.refresh(user)

        return SignupOut(id=user.id, email=getattr(user, email_col_name))

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
        raise HTTPException(status_code=500, detail=f"auth.import_error: {_import_error}")

    # Use the same column detection for login
    email_col_name, _ = _find_col(["email", "user_email", "username"])
    pass_col_name, _ = _find_col(["password", "password_hash", "hashed_password"])
    if not email_col_name or not pass_col_name:
        raise HTTPException(status_code=500, detail="auth.model_mismatch (login)")

    try:
        user = db.query(User).filter(getattr(User, email_col_name) == payload.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not verify_password(payload.password, getattr(user, pass_col_name)):  # type: ignore[arg-type]
            raise HTTPException(status_code=400, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id), "email": getattr(user, email_col_name)})
        return LoginOut(ok=True, access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"auth.login_error: {e.__class__.__name__}: {e}")
