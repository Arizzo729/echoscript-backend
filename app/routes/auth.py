from __future__ import annotations
import os, secrets
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# --- In-memory stub (per process). Good for wiring tests. ---
_USERS: Dict[str, Dict] = {}  # email -> {id, email, password, token}

# --- Cookie config (Netlify -> API cross-site) ---
COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "access_token")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".echoscript.ai")
COOKIE_SECURE = True
COOKIE_SAMESITE = "none"  # allow cross-site cookie

def _set_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        domain=COOKIE_DOMAIN,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * 30,  # 30 days
    )

def _clear_cookie(resp: Response) -> None:
    resp.delete_cookie(key=COOKIE_NAME, domain=COOKIE_DOMAIN)

def _token_from_request(req: Request) -> Optional[str]:
    auth = req.headers.get("authorization") or req.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return req.cookies.get(COOKIE_NAME)

# --- Schemas ---
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
    id: Optional[int] = None
    email: Optional[EmailStr] = None
    mode: str

# --- Routes (stubbed) ---
@router.get("/me", response_model=MeOut, summary="Return the current user (stub)")
def me(request: Request) -> MeOut:
    tok = _token_from_request(request)
    if not tok:
        raise HTTPException(status_code=401, detail="Not authenticated")
    for u in _USERS.values():
        if u["token"] == tok:
            return MeOut(id=u["id"], email=u["email"], mode="stub")
    raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/signup", response_model=SignupOut, summary="Create a new account (stub)")
def signup(payload: SignupIn, response: Response) -> SignupOut:
    if payload.email in _USERS:
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = len(_USERS) + 1
    tok = secrets.token_urlsafe(32)
    _USERS[payload.email] = {"id": uid, "email": payload.email, "password": payload.password, "token": tok}
    _set_cookie(response, tok)
    return SignupOut(id=uid, email=payload.email)

@router.post("/login", response_model=LoginOut, summary="Login (stub)")
def login(payload: LoginIn, response: Response) -> LoginOut:
    u = _USERS.get(payload.email)
    if not u or u["password"] != payload.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    _set_cookie(response, u["token"])
    return LoginOut(ok=True, access_token=u["token"])

@router.post("/logout", summary="Logout (clear cookie)")
def logout(response: Response):
    _clear_cookie(response)
    return {"ok": True}
