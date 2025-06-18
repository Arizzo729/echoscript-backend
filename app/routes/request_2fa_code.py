from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.config import redis_client
from app.utils.send_email import send_email
from app.utils.logger import logger
import random

router = APIRouter()

class TwoFARequest(BaseModel):
    email: EmailStr

@router.post("/api/auth/request-2fa-code")
def request_2fa_code(data: TwoFARequest):
    code = str(random.randint(100000, 999999))
    key = f"2fa:{data.email}"

    try:
        redis_client.setex(key, 300, code)  # 5 min expiry
        logger.info(f"[2FA] Code sent to {data.email} → {code}")
    except Exception as e:
        logger.error(f"[2FA Redis Error] {e}")
        raise HTTPException(status_code=500, detail="Could not store 2FA code.")

    subject = "Your EchoScript.AI Login Code"
    body = f"Your 2FA code is: {code}\n\nIt expires in 5 minutes."

    try:
        send_email(to=data.email, subject=subject, content=body)
        return {"status": "ok", "message": "2FA code sent."}
    except Exception as e:
        logger.error(f"[2FA Email Error] {e}")
        raise HTTPException(status_code=500, detail="Could not send 2FA code.")
