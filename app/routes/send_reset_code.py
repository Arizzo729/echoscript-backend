from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import random
import os
from uuid import uuid4

from app.utils.send_email import send_email
from app.config import redis_client
from app.utils.logger import logger

router = APIRouter()

class VerificationRequest(BaseModel):
    email: EmailStr

@router.post("/api/auth/send-verification-code")
async def send_verification_code(data: VerificationRequest):
    email = data.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    # === Generate 6-digit Verification Code ===
    try:
        code = f"{random.randint(100000, 999999):06d}"
    except Exception:
        code = uuid4().hex[:6].upper()

    # === Store in Redis with 15 min TTL ===
    redis_key = f"verify:{email}"
    try:
        success = redis_client.setex(redis_key, 900, code)
        if not success:
            raise Exception("Redis SETEX failed")
        logger.info(f"[Verify Cache ✅] Code cached for {email} → {code}")
    except Exception as e:
        logger.exception(f"[Redis ❌] Caching error: {e}")
        raise HTTPException(status_code=500, detail="Unable to cache verification code. Please try again shortly.")

    # === Construct Email ===
    subject = "🔐 Confirm Your EchoScript.AI Account"
    content = (
        f"Hi there,\n\n"
        f"You're almost done! Use the code below to confirm your email:\n\n"
        f"🔢 <strong>{code}</strong>\n\n"
        f"This code expires in 15 minutes.\n\n"
        f"If you didn't request this, feel free to ignore it.\n\n"
        f"— The EchoScript.AI Team"
    )

    # === Send Email ===
    try:
        result = send_email(to=email, subject=subject, content=content)
        if result.get("status") != "success":
            raise RuntimeError(result.get("message", "Unknown email sending error."))

        logger.info(f"[Email ✅] Verification email delivered to {email}")
        return {
            "status": "success",
            "message": "Verification code sent. Please check your inbox."
        }

    except Exception as e:
        logger.exception(f"[Email ❌] Delivery failed to {email}: {e}")
        raise HTTPException(status_code=500, detail="Email delivery failed. Please try again.")


