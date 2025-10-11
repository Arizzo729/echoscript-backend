# app/routes/auth.py
from __future__ import annotations
import os, time, hmac, json, base64, hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.utils.auth_utils import verify_password

# NOTE: prefix is RELATIVE now (no /api). main.py will mount at /api and /v1.
router = APIRouter(prefix="/auth", tags=["Auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_DEV_ONLY")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "2592000"))

COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "access_token")
COOKIE_DOMAIN = (os.getenv("COOKIE_DOMAIN", ".echoscript.ai") or ".echoscript.ai").strip()
COOKIE_SECURE = True
COOKIE_SAMESITE = "none"
COOKIE_PATH = "/"

def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))

def _sign(msg: bytes) -> str:
    sig = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    return _b64u_encode(sig)

def _create_jwt(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    body = {**payload, "iat": now, "exp": now + JWT_TTL_SECONDS}
    h64 = _b64u_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p64 = _b64u_encode(json.dumps(body,   separators=(",", ":")).encode("utf-8"))
    sig = _sign(f"{h64}.{p64}".encode("utf-8"))
    return f"{h64}.{p64}.{sig}"

def _verify_jwt(token: str) -> Dict[str, Any]:
    try:
        h64, p64, s = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    expected = _sign(f"{h64}.{p64}".encode("utf-8"))
    if not hmac.compare_digest(expected, s):
        raise HTTPException(status_code=401, detail="Invalid signature")
    payload = json.loads(_b64u_decode(p64))
    if int(time.time()) >= int(payload.get("exp", 0)):
        raise HTTPException(status_code=401, detail="Token expired")
    return payload

def _user_id_for(email: str) -> int:
    # (Used for legacy tokens; new tokens use actual DB user ID)
    h = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _set_cookie(resp: Response, token: str) -> None:
    expires = datetime.now(timezone.utc) + timedelta(seconds=JWT_TTL_SECONDS)
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        domain=COOKIE_DOMAIN,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=JWT_TTL_SECONDS,
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )

def _clear_cookie(resp: Response) -> None:
    resp.delete_cookie(key=COOKIE_NAME, domain=COOKIE_DOMAIN, path=COOKIE_PATH)

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
    mode: str = "jwt"

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> LoginOut:
    # Verify user credentials against the database
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = _create_jwt({"sub": str(user.id), "email": user.email})
    _set_cookie(response, token)
    return LoginOut(ok=True, access_token=token)

@router.post("/logout")
def logout(response: Response):
    _clear_cookie(response)
    return {"ok": True}

@router.get("/me", response_model=MeOut)
def me(request: Request) -> MeOut:
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = _verify_jwt(token)
    return MeOut(id=int(data["sub"]), email=data["email"], mode="jwt")

