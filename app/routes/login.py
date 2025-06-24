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
    throttle_key = f"login:attempts:{email}"

    # === Rate Limiting (5 attempts/hr) ===
    try:
        attempts = redis_client.incr(throttle_key)
        if attempts == 1:
            redis_client.expire(throttle_key, 3600)
        if attempts > 5:
            logger.warning(f"[Login] ❌ Too many attempts for {email}")
            raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
    except Exception as e:
        logger.warning(f"[Login Throttle] Redis issue for {email}: {e}")

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Your account has been disabled. Contact support.")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Your account is not verified. Check your inbox.")

        logger.info(f"[Login] ✅ {email} logged in @ {datetime.utcnow().isoformat()}")

        token = create_jwt_token(user_id=user.id, email=user.email, plan=user.plan)

        return {
            "status": "success",
            "message": "Welcome back! You are now logged in.",
            "user": {
                "id": user.id,
                "email": user.email,
                "plan": user.plan,
                "is_verified": user.is_verified
            },
            "token": token
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Login Error] Unexpected failure for {email}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login.")