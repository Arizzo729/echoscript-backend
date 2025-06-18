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

    # Store in Redis for 15 minutes
    redis_key = f"verify:{data.email}"
    try:
        redis_client.setex(redis_key, 900, code)
        logger.info(f"[Verify] Code for {data.email} → {code}")
    except Exception as e:
        logger.error(f"[Redis Error] Failed to store verification code: {e}")
        raise HTTPException(status_code=500, detail="Unable to store verification code.")

    # Email the code
    subject = "Verify Your EchoScript.AI Email"
    content = (
        f"Hello,\n\n"
        f"Please verify your email for EchoScript.AI using the code below:\n\n"
        f"🔐 Verification Code: {code}\n\n"
        f"This code is valid for 15 minutes.\n\n"
        f"Thank you,\nEchoScript.AI Team"
    )

    try:
        result = send_email(to=data.email, subject=subject, content=content)
        if result.get("status") != "success":
            raise Exception(result.get("message", "Failed to send email"))
        return {"status": "ok", "message": "Verification code sent."}
    except Exception as e:
        logger.error(f"[Email Error] Could not send verification email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email.")

