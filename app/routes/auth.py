# app/routes/auth.py
from __future__ import annotations
import os, time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.db import get_db
from app.models import User
from app.utils.auth_utils import verify_password
from app.config import config

# NOTE: prefix is RELATIVE now (no /api). main.py will mount at /api and /v1.
router = APIRouter(prefix="/auth", tags=["Auth"])

JWT_SECRET = config.JWT_SECRET_KEY or os.getenv("JWT_SECRET", "CHANGE_ME_DEV_ONLY")
JWT_ALGORITHM = config.JWT_ALGORITHM or "HS256"
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "2592000"))

COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "access_token")

def _get_cookie_domain(request: Request) -> str:
    """Dynamically determine cookie domain from request origin"""
    # Try environment variable first
    env_domain = (os.getenv("COOKIE_DOMAIN") or "").strip()
    if env_domain:
        return env_domain
    
    # Extract domain from request host
    host = request.headers.get("host", "localhost").split(":")[0]  # Remove port
    
    # For localhost/127.0.0.1, don't set domain (browser default)
    if host in ("localhost", "127.0.0.1", "::1"):
        return None
    
    # For other domains, use the domain as-is
    return host

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
COOKIE_PATH = "/"

def _create_jwt(payload: Dict[str, Any]) -> str:
    """Create JWT token using python-jose library (compatible with asgi_dev.py)"""
    now = int(time.time())
    to_encode = {**payload, "iat": now, "exp": now + JWT_TTL_SECONDS}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _verify_jwt(token: str) -> Dict[str, Any]:
    """Verify JWT token using python-jose library (compatible with asgi_dev.py)"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def _set_cookie(resp: Response, token: str, request: Request) -> None:
    expires = datetime.now(timezone.utc) + timedelta(seconds=JWT_TTL_SECONDS)
    cookie_domain = _get_cookie_domain(request)
    
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        domain=cookie_domain,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=JWT_TTL_SECONDS,
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )

def _clear_cookie(resp: Response, request: Request) -> None:
    cookie_domain = _get_cookie_domain(request)
    resp.delete_cookie(key=COOKIE_NAME, domain=cookie_domain, path=COOKIE_PATH)

def _token_from_request(req: Request) -> Optional[str]:
    auth = req.headers.get("authorization") or req.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return req.cookies.get(COOKIE_NAME)

class LoginIn(BaseModel):
    email: str
    password: str

class LoginOut(BaseModel):
    ok: bool
    access_token: str
    token_type: str = "bearer"

class MeOut(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    username: Optional[str] = None
    plan: Optional[str] = "Free"
    avatar_url: Optional[str] = None
    mode: str = "jwt"

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> LoginOut:
    import logging
    log = logging.getLogger(__name__)
    
    try:
        # Verify user credentials against the database
        user = db.query(User).filter(User.email == payload.email).one_or_none()
        
        if not user:
            log.warning(f"Login attempt with non-existent email: {payload.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Ensure password field exists and is not None
        if not hasattr(user, 'password'):
            log.error(f"User model missing password attribute")
            raise HTTPException(status_code=500, detail="Server configuration error")
        
        if user.password is None or user.password == "":
            log.warning(f"User {user.email} has no password set")
            raise HTTPException(status_code=401, detail="Password not set. Please use 'Forgot Password' to set one.")
        
        if user.password.startswith("PLACEHOLDER"):
            log.warning(f"User {user.email} has placeholder password")
            raise HTTPException(status_code=401, detail="Password not set. Please use 'Forgot Password' to set one.")
        
        if not verify_password(payload.password, user.password):
            log.warning(f"Invalid password for user: {user.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = _create_jwt({"sub": str(user.id), "email": user.email})
        _set_cookie(response, token, request)
        return LoginOut(ok=True, access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Login error for email {payload.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@router.post("/logout")
def logout(request: Request, response: Response):
    _clear_cookie(response, request)
    return {"ok": True}

@router.get("/me", response_model=MeOut)
def me(request: Request, db: Session = Depends(get_db)) -> MeOut:
    import logging
    log = logging.getLogger(__name__)
    try:
        token = _token_from_request(request)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        data = _verify_jwt(token)
        user_id = int(data["sub"])
        user = db.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return MeOut(
            id=user.id, 
            email=user.email, 
            name=getattr(user, "username", None),
            username=getattr(user, "username", None),
            plan=getattr(user, "plan", "Free") or "Free",
            avatar_url=getattr(user, "avatar_url", None),
            mode="jwt"
        )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error in /me endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/signin", response_model=LoginOut)
def signin(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> LoginOut:
    return login(payload, request, response, db)

@router.post("/refresh", response_model=LoginOut)
def refresh(request: Request, response: Response) -> LoginOut:
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = _verify_jwt(token)
    new_token = _create_jwt({"sub": data["sub"], "email": data["email"]})
    _set_cookie(response, new_token, request)
    return LoginOut(ok=True, access_token=new_token)

