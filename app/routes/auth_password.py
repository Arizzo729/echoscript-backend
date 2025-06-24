# === routes/auth/verify_reset.py — EchoScript.AI Secure Password Reset Verification ===

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from app.db import get_db
from app.models import User
from app.auth_utils import hash_password
from app.utils.logger import logger
from app.config import redis_client

router = APIRouter(prefix="/auth", tags=["Authentication"])

class VerifyReset(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=10)
    new_password: constr(min_length=8, max_length=64)

@router.post("/verify-reset")
def verify_reset(data: VerifyReset, request: Request, db: Session = Depends(get_db)):
    try:
        ip = request.client.host

        # Validate reset code
        key = f"reset:{data.email}"
        stored_code = redis_client.get(key)
        if not stored_code:
            logger.warning(f"[Reset] Code expired for {data.email} from IP {ip}")
            raise HTTPException(status_code=410, detail="Reset code expired or invalid.")
        if stored_code.decode() != data.code:
            logger.warning(f"[Reset] Invalid code attempt for {data.email} from IP {ip}")
            raise HTTPException(status_code=401, detail="Invalid reset code.")

        # Find user
        user = db.query(User).filter(User.email == data.email).first()
        if not user:
            logger.warning(f"[Reset] User not found: {data.email}")
            raise HTTPException(status_code=404, detail="User not found.")

        # Update password securely
        user.password = hash_password(data.new_password)
        db.commit()
        redis_client.delete(key)

        logger.info(f"[Reset] ✅ Password reset for {data.email} from IP {ip}")
        return {"status": "success", "message": "Password reset successful."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Reset Error] Unexpected failure: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during password reset.")


