# ---- EchoScript.AI: routes/verify_reset.py ----

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_user_by_email, update_user_password
from app.auth.auth_utils import hash_password
from app.config import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# === Request Schema ===
class VerifyResetRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# === Password Reset Verification ===
@router.post("/verify-reset", response_model=dict)
async def verify_reset(data: VerifyResetRequest):
    key = f"reset:{data.email}"

    if not redis_client:
        logger.error("❌ Redis not connected. Cannot verify reset code.")
        raise HTTPException(status_code=500, detail="Internal server error")

    try:
        saved_code = redis_client.get(key)

        if not saved_code:
            logger.warning(f"⚠️ Reset code missing or expired for {data.email}")
            raise HTTPException(status_code=400, detail="Reset code expired or invalid")

        if saved_code.decode() != data.code:
            logger.warning(f"❌ Invalid reset code for {data.email}")
            raise HTTPException(status_code=400, detail="Invalid reset code")

        user = get_user_by_email(data.email)
        if not user:
            logger.warning(f"❌ Attempted reset for unknown user: {data.email}")
            raise HTTPException(status_code=404, detail="User not found")

        hashed_pw = hash_password(data.new_password)
        if not update_user_password(data.email, hashed_pw):
            logger.error(f"❌ Failed to update password for {data.email}")
            raise HTTPException(status_code=500, detail="Failed to update password")

        redis_client.delete(key)
        logger.info(f"✅ Password reset successful for {data.email}")
        return {"status": "ok"}

    except HTTPException:
        raise  # Let FastAPI handle known errors cleanly
    except Exception as e:
        logger.exception(f"❌ Unexpected error during password reset for {data.email}: {e}")
        raise HTTPException(status_code=500, detail="Reset failed. Please try again later.")
