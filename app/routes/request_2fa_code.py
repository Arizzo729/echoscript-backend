from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.config import redis_client
from app.utils.send_email import send_email
from app.utils.logger import logger
import random

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# === Request Schema ===
class TwoFARequest(BaseModel):
    email: EmailStr

# === Route: Request 2FA Code ===
@router.post("/request-2fa-code", response_model=dict)
def request_2fa_code(data: TwoFARequest):
    code = f"{random.randint(100000, 999999):06d}"
    redis_key = f"2fa:{data.email}"

    # === Step 1: Store in Redis ===
    try:
        result = redis_client.setex(redis_key, 300, code)  # 5 min expiry
        if not result:
            raise Exception("Redis setex returned False")
        logger.info(f"[2FA] Code cached for {data.email} → {code}")
    except Exception as e:
        logger.error(f"[2FA Redis ❌] Failed to store code: {e}")
        raise HTTPException(status_code=500, detail="Unable to store 2FA code.")

    # === Step 2: Send Email ===
    subject = "🔐 Your EchoScript.AI Login Code"
    content = (
        f"Hello,\n\n"
        f"Use the code below to complete your login:\n\n"
        f"🔢 Your 2FA Code: {code}\n\n"
        f"This code is valid for 5 minutes.\n\n"
        f"If you didn’t request this, please ignore this message.\n\n"
        f"— EchoScript.AI Security Team"
    )

    try:
        result = send_email(to=data.email, subject=subject, content=content)
        if result.get("status") != "success":
            raise Exception(result.get("message", "Failed to send email"))
        return {"status": "ok", "message": "2FA code sent successfully."}
    except Exception as e:
        logger.error(f"[2FA Email ❌] Failed to send to {data.email}: {e}")
        raise HTTPException(status_code=500, detail="Unable to send 2FA email.")

