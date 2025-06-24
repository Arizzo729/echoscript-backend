from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import User
from app.auth_utils import hash_password
from app.utils.logger import logger
from app.utils.send_email import send_email
from app.config import redis_client
import string, secrets
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["Authentication"])

# === Request Schema ===
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

# === Signup Endpoint ===
@router.post("/signup")
def signup(data: SignUpRequest, request: Request, db: Session = Depends(get_db)):
    email = data.email.strip().lower()

    if db.query(User).filter(User.email == email).first():
        logger.info(f"[Signup ❌] Duplicate email attempt: {email}")
        raise HTTPException(status_code=400, detail="Email already registered.")

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    throttle_key = f"signup:attempts:{email}"
    try:
        attempts = redis_client.incr(throttle_key)
        if attempts == 1:
            redis_client.expire(throttle_key, 3600)
        if attempts > 5:
            logger.warning(f"[Signup Throttle] Too many attempts for {email}")
            raise HTTPException(status_code=429, detail="Too many signup attempts. Try again later.")
    except Exception as e:
        logger.warning(f"[Throttle Error] Redis issue for {email}: {e}")

    try:
        hashed_pw = hash_password(data.password)
        new_user = User(
            email=email,
            password=hashed_pw,
            is_verified=False,
            is_active=True,
            plan="guest"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[Signup ✅] Registered: {email}")

        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        redis_key = f"verify:{email}"

        if not redis_client.setex(redis_key, 900, code):
            raise RuntimeError("Verification code caching failed.")

        logger.info(f"[Verify Code] Cached for {email} → {code}")

        subject = "🔐 Verify Your EchoScript.AI Account"
        content = (
            f"Hi {email},\n\n"
            f"Thanks for signing up for EchoScript.AI.\n\n"
            f"Your verification code is: <strong>{code}</strong>\n\n"
            f"This code is valid for 15 minutes.\n\n"
            f"If you didn’t request this account, you may safely ignore this email.\n\n"
            f"— EchoScript.AI Security"
        )

        email_status = send_email(to=email, subject=subject, content=content)
        if email_status.get("status") != "success":
            logger.warning(f"[Email ❌] Could not deliver to {email}: {email_status}")
            raise RuntimeError("Verification email failed to send.")

        return {
            "status": "success",
            "message": "Signup complete. Verification code sent to your email."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Signup Error] {email} — {e}")
        raise HTTPException(status_code=500, detail="Signup failed due to an internal error.")

