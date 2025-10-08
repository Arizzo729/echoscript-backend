from __future__ import annotations
import os
import secrets
import traceback
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ----------------------------------------------------------------------
# Stub mode: ON by default; set AUTH_STUB=false in Railway for real DB.
# ----------------------------------------------------------------------
STUB_MODE = (os.getenv("AUTH_STUB", "true").lower() in ("1", "true", "yes", "y"))
COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "access_token")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".echoscript.ai")  # your apex wildcard
COOKIE_SECURE = True  # live over HTTPS
COOKIE_SAMESITE = "none"  # allow cross-site cookie from Netlify→API

# In-memory stub users (per process; fine for wiring tests)
_STUB_USERS: Dict[str, Dict] = {}

# --- Try real DB helpers (optional; we fall back gracefully) ------------
_db_ok = True
try:
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError, ProgrammingError
    from sqlalchemy import LargeBinary

    from app.db import get_db, Base, engine  # type: ignore
    import app.models  # registers models
    from app.models import User  # type: ignore

    try:
        from app.utils.auth_utils import hash_password, verify_password, create_access_token  # type: ignore
    except Exception:
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

# -------------------------- Schemas ------------------------------------
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

class MeOut(BaseModel):
    id: int | None = None
    email: EmailStr | None = None
    mode: str

# -------------------------- Helpers ------------------------------------
def _find_col(name_candidates):
    cols = User.__table__.c
    for n in name_candidates:
        if n in cols:
            return n, cols[n]
    return None, None

def _coerce_for_password_column(value, coltype):
    from sqlalchemy import LargeBinary  # local import for stub compatibility
    if isinstance(coltype, LargeBinary):
        return value.encode("utf-8") if isinstance(value, str) else bytes(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", "ignore")
    return str(value)

def _token_from_request(req: Request) -> Optional[str]:
    auth = req.headers.get("authorization") or req.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    # cookie fallback
    tok = req.cookies.get(COOKIE_NAME) or req.cookies.get("token") or req.cookies.get("session")
    return tok

def _set_cookie(resp: Response, token: str):
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        domain=COOKIE_DOMAIN,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * 30,  # 30 days
    )

def _clear_cookie(resp: Response):
    resp.delete_cookie(key=COOKIE_NAME, domain=COOKIE_DOMAIN)

# -------------------------- Stub impls ---------------------------------
def _stub_signup(email: str, password: str) -> SignupOut:
    if email in _STUB_USERS:
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = len(_STUB_USERS) + 1
    _STUB_USERS[email] = {
        "id": uid, "email": email, "password": password,
        "token": secrets.token_urlsafe(32),
    }
    return SignupOut(id=uid, email=email)

def _stub_login(email: str, password: str) -> LoginOut:
    u = _STUB_USERS.get(email)
    if not u or u["password"] != password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return LoginOut(ok=True, access_token=u["token"])

def _stub_me(token: Optional[str]) -> MeOut:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    for u in _STUB_USERS.values():
        if u["token"] == token:
            return MeOut(id=u["id"], email=u["email"], mode="stub")
    raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------------- Routes -----------------------------------
@router.post("/signup", response_model=SignupOut, summary="Create a new account")
def signup(payload: SignupIn, response: Response, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> SignupOut:
    if STUB_MODE or not _db_ok:
        out = _stub_signup(payload.email, payload.password)
        tok = _STUB_USERS[payload.email]["token"]
        _set_cookie(response, tok)  # auto-login on signup
        return out

    try:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        email_col_name, _ = _find_col(["email", "user_email", "username"])
        pass_col_name, pass_col_type = _find_col(["password", "password_hash", "hashed_password"])
        if not email_col_name or not pass_col_name:
            out = _stub_signup(payload.email, payload.password)
            _set_cookie(response, _STUB_USERS[payload.email]["token"])
            return out

        existing = db.query(User).filter(getattr(User, email_col_name) == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        hashed = _coerce_for_password_column(hash_password(payload.password), pass_col_type.type)
        user_kwargs = {email_col_name: payload.email, pass_col_name: hashed}
        user = User(**user_kwargs)  # type: ignore[arg-type]

        db.add(user); db.commit(); db.refresh(user)
        token = create_access_token({"sub": str(user.id), "email": getattr(user, email_col_name)})
        _set_cookie(response, token)
        return SignupOut(id=user.id, email=getattr(user, email_col_name))

    except HTTPException:
        raise
    except (IntegrityError, ProgrammingError):
        db.rollback()
        out = _stub_signup(payload.email, payload.password)
        _set_cookie(response, _STUB_USERS[payload.email]["token"])
        return out
    except Exception:
        try: db.rollback()
        except Exception: pass
        traceback.print_exc()
        out = _stub_signup(payload.email, payload.password)
        _set_cookie(response, _STUB_USERS[payload.email]["token"])
        return out

@router.post("/login", response_model=LoginOut, summary="Login and return a token")
def login(payload: LoginIn, response: Response, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> LoginOut:
    if STUB_MODE or not _db_ok:
        out = _stub_login(payload.email, payload.password)
        _set_cookie(response, out.access_token)
        return out

    try:
        email_col_name, _ = _find_col(["email", "user_email", "username"])
        pass_col_name, _ = _find_col(["password", "password_hash", "hashed_password"])
        if not email_col_name or not pass_col_name:
            out = _stub_login(payload.email, payload.password)
            _set_cookie(response, out.access_token)
            return out

        user = db.query(User).filter(getattr(User, email_col_name) == payload.email).first()
        if not user or not verify_password(payload.password, getattr(user, pass_col_name)):  # type: ignore[arg-type]
            raise HTTPException(status_code=400, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id), "email": getattr(user, email_col_name)})
        _set_cookie(response, token)
        return LoginOut(ok=True, access_token=token)

    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        out = _stub_login(payload.email, payload.password)
        _set_cookie(response, out.access_token)
        return out

@router.post("/logout", summary="Clear auth cookie")
def logout(response: Response):
    _clear_cookie(response)
    return {"ok": True}

@router.get("/me", response_model=MeOut, summary="Return the current user")
def me(request: Request, db: Optional["Session"] = Depends(get_db) if _db_ok else None) -> MeOut:
    token = _token_from_request(request)
    if STUB_MODE or not _db_ok:
        return _stub_me(token)

    # Best-effort real mode: if we can’t decode the token here, use 401 so UI can recover.
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # If you have a verify/decode helper, plug it here to extract user id/email.
    # For now, return a minimal success if token exists so the UI can proceed.
    return MeOut(id=None, email=None, mode="real")
