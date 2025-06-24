# === routes/auth/login.py — EchoScript.AI Secure Login ===

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import User
from app.auth_utils import verify_password, create_jwt_token
from app.utils.logger import logger
from app.config import redis_client
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

# === Request Schema ===
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# === Login Endpoint ===
@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    email = data.email.strip().lower()

    # === Rate Limiting (5 attempts/hr) ===
    throttle_key = f"login:attempts:{email}"
    try:
        attempts = redis_client.incr(throttle_key)
        if attempts == 1:
            redis_client.expire(throttle_key, 3600)  # 1 hour expiry
        if attempts > 5:
            logger.warning(f"[Login] Too many attempts for {email}")
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again in an hour.")
    except Exception as e:
        logger.warning(f"[Throttle] Redis error for {email}: {e}")

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        if not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled.")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Account not verified. Please check your email.")

        # === Successful Login ===
        logger.info(f"[Login] ✅ {email} logged in at {datetime.utcnow().isoformat()}")

        # === Optional JWT Session Token ===
        token = create_jwt_token(user_id=user.id, email=user.email, plan=user.plan)

        return {
            "status": "ok",
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "email": user.email,
                "plan": user.plan,
                "is_verified": user.is_verified,
            },
            "token": token
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[Login Error] {email} — {e}")
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")
