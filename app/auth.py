# ---- EchoScript.AI Backend: auth_routes.py ----

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from app.auth.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ⚠️ TEMP: In-memory user store — replace with DB/Redis later
fake_users = {
    "guest@echoscript.ai": hash_password("guest"),
}

# -----------------------------
# Schemas
# -----------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    token: str


# -----------------------------
# GET /guest → token for guest
# -----------------------------
@router.get("/guest")
def guest_login():
    guest_email = "guest@echoscript.ai"
    token = create_access_token({"sub": guest_email}, expires_delta=timedelta(hours=6))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": guest_email,
            "plan": "guest",
            "name": "Guest",
        },
    }


# -----------------------------
# POST /register
# -----------------------------
@router.post("/register")
def register(user: UserRegister):
    if user.email in fake_users:
        raise HTTPException(status_code=400, detail="Email already registered.")
    fake_users[user.email] = hash_password(user.password)
    return {
        "message": "✅ Registration successful",
        "email": user.email,
    }


# -----------------------------
# POST /login
# -----------------------------
@router.post("/login")
def login(user: UserLogin):
    stored_hash = fake_users.get(user.email)
    if not stored_hash or not verify_password(user.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": user.email}, expires_delta=timedelta(hours=12))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "plan": "free" if user.email != "guest@echoscript.ai" else "guest",
            "name": user.email.split("@")[0].title(),
        },
    }


# -----------------------------
# POST /refresh
# -----------------------------
@router.post("/refresh")
def refresh_token(data: TokenRefreshRequest):
    decoded = decode_token(data.token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    new_token = create_access_token({"sub": decoded["sub"]}, expires_delta=timedelta(hours=12))
    return {
        "access_token": new_token,
        "token_type": "bearer",
    }

