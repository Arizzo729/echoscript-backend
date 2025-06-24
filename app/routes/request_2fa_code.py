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
        success = redis_client.setex(redis_key, 300, code)  # 5-minute expiry
        if not success:
            raise Exception("Redis setex operation failed.")
        logger.info(f"[2FA] ✅ Code stored in Redis for {data.email} → {code}")
    except Exception as e:
        logger.exception(f"[2FA Redis ❌] Failed to cache 2FA code: {e}")
        raise HTTPException(status_code=500, detail="Unable to cache 2FA code.")

    # === Step 2: Send Email ===
    subject = "🔐 Your EchoScript.AI Login Code"
    content = (
        f"Hello,\n\n"
        f"Use the code below to verify your login and access your account:\n\n"
        f"🔢 <strong>{code}</strong>\n\n"
        f"This code is valid for 5 minutes.\n\n"
        f"If you did not request this code, please ignore this email.\n\n"
        f"Thank you,\nThe EchoScript.AI Security Team"
    )

    try:
        result = send_email(to=data.email, subject=subject, content=content)
        if result.get("status") != "success":
            raise Exception(result.get("message", "Failed to send email"))
        logger.info(f"[2FA Email ✅] Sent successfully to {data.email}")
        return {"status": "success", "message": "2FA code sent successfully."}
    except Exception as e:
        logger.exception(f"[2FA Email ❌] Delivery failed to {data.email}: {e}")
        raise HTTPException(status_code=500, detail="Unable to send 2FA email.")

