# routes/auth/send_verification_code.py — EchoScript.AI Email Verification Code Sender

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
    if not data.email:
        raise HTTPException(status_code=400, detail="Email is required.")

    try:
        # Generate 6-digit verification code
        code = str(random.randint(100000, 999999))
    except:
        code = uuid4().hex[:6]

    # === Store in Redis for 15 minutes ===
redis_key = f"verify:{data.email.lower()}"
try:
    redis_client.setex(redis_key, 900, code)
    logger.info(f"[Verify] Verification code cached for {data.email} → {code}")
except Exception as e:
    logger.error(f"[Redis ❌] Failed to store verification code: {e}")
    raise HTTPException(status_code=500, detail="Unable to cache verification code. Try again shortly.")

# === Prepare Email Content ===
subject = "Verify Your EchoScript.AI Email"
content = (
    f"Hello,\n\n"
    f"Thanks for signing up with EchoScript.AI!\n\n"
    f"🔐 Your verification code: {code}\n\n"
    f"This code will expire in 15 minutes.\n\n"
    f"If you didn’t create this account, you can safely ignore this email.\n\n"
    f"— EchoScript.AI Team"
)

# === Send Email ===
try:
    email_response = send_email(to=data.email, subject=subject, content=content)
    if email_response.get("status") != "success":
        raise RuntimeError(email_response.get("message", "Unknown failure during email send."))

    logger.info(f"[Email ✅] Verification email sent to {data.email}")
    return {
        "status": "ok",
        "message": "Verification code sent successfully. Check your inbox."
    }

except Exception as e:
    logger.error(f"[Email ❌] Failed to send to {data.email}: {e}")
    raise HTTPException(status_code=500, detail="Failed to send verification email.")


