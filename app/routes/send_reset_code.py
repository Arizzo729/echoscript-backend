from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import random
import os
from app.utils.send_email import send_email  # We'll create this helper
from app.config import redis_client  # Redis or fallback

router = APIRouter()

class ResetRequest(BaseModel):
    email: EmailStr

@router.post("/api/auth/send-reset-code")
async def send_reset_code(data: ResetRequest):
    code = str(random.randint(100000, 999999))
    redis_client.setex(f"reset:{data.email}", 900, code)  # 15 minutes

    subject = "Your EchoScript Reset Code"
    content = f"Your EchoScript password reset code is: {code}"

    try:
        send_email(to=data.email, subject=subject, content=content)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
