# auth_routes.py — EchoScript.AI Authentication API

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from app.auth.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ⚠️ TEMPORARY: In-memory store — replace with DB or Redis session
fake_users = {
    "guest@echoscript.ai": hash_password("guest"),
}

# ==== Schemas ====

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    token: str

# ==== Routes ====

@router.get("/guest")
def guest_login():
    guest_email = "guest@echoscript.ai"
    access_token = create_access_token({"sub": guest_email}, expires_delta=timedelta(hours=6))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": guest_email,
            "plan": "guest",
            "name": "Guest",
        },
    }

@router.post("/register")
def register(user: UserRegister):
    if user.email in fake_users:
        raise HTTPException(status_code=400, detail="Email already registered.")

    fake_users[user.email] = hash_password(user.password)

    return {
        "message": "✅ Registration successful",
        "email": user.email,
    }

@router.post("/login")
def login(user: UserLogin):
    stored_hash = fake_users.get(user.email)

    if not stored_hash or not verify_password(user.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token({"sub": user.email}, expires_delta=timedelta(hours=12))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "plan": "guest" if user.email == "guest@echoscript.ai" else "free",
            "name": user.email.split("@")[0].title(),
        },
    }

@router.post("/refresh")
def refresh_token(data: TokenRefreshRequest):
    decoded = decode_token(data.token)
    if not decoded or "sub" not in decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    refreshed_token = create_access_token({"sub": decoded["sub"]}, expires_delta=timedelta(hours=12))

    return {
        "access_token": refreshed_token,
        "token_type": "bearer",
    }
