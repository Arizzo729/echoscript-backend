# routes/auth/reset_password_request.py — EchoScript.AI Password Reset (Send Code)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import random
import os
from uuid import uuid4

from app.utils.send_email import send_email
from app.utils.logger import logger
from app.config import redis_client

router = APIRouter()

class ResetRequest(BaseModel):
    email: EmailStr

@router.post("/api/auth/send-reset-code")
async def send_reset_code(data: ResetRequest):
    if not data.email:
        raise HTTPException(status_code=400, detail="Email is required.")

    # Generate 6-digit numeric code
    try:
        code = str(random.randint(100000, 999999))
    except:
        code = uuid4().hex[:6]

    # Cache code in Redis for 15 min
    try:
        key = f"reset:{data.email}"
        redis_client.setex(key, 900, code)
        logger.info(f"[Reset] Code generated for {data.email} → {code}")
    except Exception as e:
        logger.error(f"[Redis Error] Failed to store reset code: {e}")
        raise HTTPException(status_code=500, detail="Server error: cannot store reset code.")

    # Email the code
    subject = "Your EchoScript.AI Reset Code"
    content = f"Hello,\n\nHere is your EchoScript password reset code: {code}\nThis code is valid for 15 minutes.\n\nThanks,\nEchoScript.AI Team"

    try:
        result = send_email(to=data.email, subject=subject, content=content)
        if result.get("status") != "success":
            raise Exception(result.get("message", "Failed to send email"))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"[Email Error] Could not send reset email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email.")
