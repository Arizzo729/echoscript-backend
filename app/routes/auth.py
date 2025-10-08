from __future__ import annotations
import os, time, hmac, json, base64, hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ===================== Config =====================
# Use your existing JWT secret; token stays valid across restarts.
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_DEV_ONLY")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "2592000"))  # 30 days

# Cookie attributes for cross-subdomain (site <-> api)
COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "access_token")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".echoscript.ai").strip() or ".echoscript.ai"
COOKIE_SECURE = True
COOKIE_SAMESITE = "none"  # allow cross-subdomain
COOKIE_PATH = "/"

# ===================== Tiny JWT (HS256) =====================
def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))

def _sign(msg: bytes) -> str:
    sig = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    return _b64u_encode(sig)

def create_jwt(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    exp = now + JWT_TTL_SECONDS
    body = {**payload, "iat": now, "exp": exp}
    h64 = _b64u_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p64 = _b64u_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    sig = _sign(f"{h64}.{p64}".encode("utf-8"))
    return f"{h64}.{p64}.{sig}"

def verify_jwt(token: str) -> Dict[str, Any]:
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

# ===================== Helpers =====================
def _user_id_for(email: str) -> int:
    # deterministic id from email (stable across restarts)
    h = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _set_cookie(resp: Response, token: str):
    # Set both Expires and Max-Age for broad browser compatibility.
    expires = (datetime.now(timezone.utc) + timedelta(seconds=JWT_TTL_SECONDS))
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

def _clear_cookie(resp: Response):
    # Expire cookie immediately
    resp.delete_cookie(key=COOKIE_NAME, domain=COOKIE_DOMAIN, path=COOKIE_PATH)

def _token_from_request(req: Request) -> Optional[str]:
    auth = req.headers.get("authorization") or req.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return req.cookies.get(COOKIE_NAME)

# ===================== Schemas =====================
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
    id: int
    email: EmailStr
    mode: str = "jwt"

# ===================== Routes =====================
@router.post("/signup", response_model=SignupOut, summary="Create account (stateless JWT)")
def signup(payload: SignupIn, response: Response) -> SignupOut:
    # In this stateless stub, we don't persist users; we just mint a signed token.
    uid = _user_id_for(payload.email)
    token = create_jwt({"sub": str(uid), "email": payload.email})
    _set_cookie(response, token)
    return SignupOut(id=uid, email=payload.email)

@router.post("/login", response_model=LoginOut, summary="Login (stateless JWT)")
def login(payload: LoginIn, response: Response) -> LoginOut:
    # Stub: accept any email/password and mint a token.
    # (Wire real password checks later; JWT remains compatible.)
    uid = _user_id_for(payload.email)
    token = create_jwt({"sub": str(uid), "email": payload.email})
    _set_cookie(response, token)
    return LoginOut(ok=True, access_token=token)

@router.post("/logout", summary="Clear auth cookie")
def logout(response: Response):
    _clear_cookie(response)
    return {"ok": True}

@router.get("/me", response_model=MeOut, summary="Return current user (from JWT cookie)")
def me(request: Request) -> MeOut:
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = verify_jwt(token)
    uid = int(data["sub"])
    email = EmailStr(data["email"])
    return MeOut(id=uid, email=email, mode="jwt")

