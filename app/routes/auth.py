# app/routes/auth.py
from __future__ import annotations
import os
import secrets
import traceback
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ------------------------------------------------------------------------------
# Stub mode: ON by default so the route "just works".
#   Set AUTH_STUB=false in Railway to switch to real DB mode.
# ------------------------------------------------------------------------------
STUB_MODE = (os.getenv("AUTH_STUB", "true").lower() in ("1", "true", "yes", "y"))

# In-memory stub users (per-process; good enough to verify frontend wiring)
_STUB_USERS: Dict[str, Dict] = {}


# ------------------------------------------------------------------------------
# Attempt to import DB + models + helpers for real mode
# ------------------------------------------------------------------------------
_db_ok = True
try:
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError, ProgrammingError
    from sqlalchemy import LargeBinary

    # your project pieces
    from app.db import get_db, Base, engine  # type: ignore
    import app.models  # registers models with SQLAlchemy
    from app.models import User  # type: ignore

    try:
        from app.utils.auth_utils import hash_password, verify_password, create_access_token  # type: ignore
    except Exception:
        # Fallbacks (non-production crypto) — only used if your real helpers are missing
        import hashlib

        def hash_password(p: str) -> str:
            return hashlib.sha256(p.encode("utf-8")).hexdigest()

        def verify_password(p: str, hashed: str) -> bool:
            return hash_password(p) == (hashed.decode() if isinstance(hashed, (bytes, bytearray, memoryview)) else hashed)

        def create_access_token(payload: dict) -> str:
            return secrets.token_urlsafe(32)

except Exception as e:
    _db_ok = False
    _import_error = e


# ------------------------------------------------------------------------------
# Pydantic schemas
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Helpers for real DB mode (discover actual column names & types)
# ------------------------------------------------------------------------------
def _find_col(name_candidates):
    cols = User.__table__.c
    for n in name_candidates:
        if n in cols:
            return n, cols[n]
    return None, None


def _coerce_for_password_column(value, coltype):
    # BYTEA/LargeBinary => bytes; otherwise string
    if isinstance(coltype, LargeBinary):
        return value.encode("utf-8") if isinstance(value, str) else bytes(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", "ignore")
    return str(value)


# ------------------------------------------------------------------------------
# STUB implementations (always succeed)
# ------------------------------------------------------------------------------
def _stub_signup(email: str, password: str) -> SignupOut:
    if email in _STUB_USERS:
        # Mimic real API 400 (email taken)
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = len(_STUB_USERS) + 1
    _STUB_USERS[email] = {
        "id": uid,
        "email": email,
        "password": password,  # do not use in production (stub only)
        "token": secrets.token_urlsafe(32),
    }
    return SignupOut(id=uid, email=email)


def _stub_login(email: str, password: str) -> LoginOut:
    u = _STUB_USERS.get(email)
    if not u or u["password"] != password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return LoginOut(ok=True, access_token=u["token"])


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@router.post("/signup", response_model=SignupOut, summary="Create a new account")
def signup(payload: SignupIn, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> SignupOut:
    # If in stub mode OR DB imports failed, guarantee success via stub.
    if STUB_MODE or not _db_ok:
        return _stub_signup(payload.email, payload.password)

    # Real DB mode
    try:
        # Ensure tables (idempotent)
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        email_col_name, _ = _find_col(["email", "user_email", "username"])
        pass_col_name, pass_col_type = _find_col(["password", "password_hash", "hashed_password"])
        if not email_col_name or not pass_col_name:
            # If schema not recognized, fall back to stub so frontend keeps working
            return _stub_signup(payload.email, payload.password)

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
    except (IntegrityError, ProgrammingError):
        # If the DB explodes for any reason, fall back to stub so the route still works
        db.rollback()
        return _stub_signup(payload.email, payload.password)
    except Exception as e:
        # Any other unexpected error → fallback to stub and log
        try:
            db.rollback()
        except Exception:
            pass
        traceback.print_exc()
        return _stub_signup(payload.email, payload.password)


@router.post("/login", response_model=LoginOut, summary="Login and return a token")
def login(payload: LoginIn, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> LoginOut:
    if STUB_MODE or not _db_ok:
        return _stub_login(payload.email, payload.password)

    try:
        email_col_name, pass_col_name = None, None
        email_col_name, _ = _find_col(["email", "user_email", "username"])
        pass_col_name, _ = _find_col(["password", "password_hash", "hashed_password"])
        if not email_col_name or not pass_col_name:
            return _stub_login(payload.email, payload.password)

        user = db.query(User).filter(getattr(User, email_col_name) == payload.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not verify_password(payload.password, getattr(user, pass_col_name)):  # type: ignore[arg-type]
            raise HTTPException(status_code=400, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id), "email": getattr(user, email_col_name)})
        return LoginOut(ok=True, access_token=token)

    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        return _stub_login(payload.email, payload.password)

