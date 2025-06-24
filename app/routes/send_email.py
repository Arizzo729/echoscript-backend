from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.config import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

# === Request Schema ===
class VerifyCodeInput(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=12)

# === Email Verification Endpoint ===
@router.post("/verify-email")
def verify_email(data: VerifyCodeInput, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    redis_key = f"verify:{email}"

    try:
        stored_code = redis_client.get(redis_key)
        if not stored_code:
            logger.warning(f"[Verify ❌] Code expired or missing for {email}")
            raise HTTPException(status_code=400, detail="Verification code expired or not found.")

        if stored_code.decode("utf-8") != data.code:
            logger.warning(f"[Verify ❌] Invalid code attempt for {email}")
            raise HTTPException(status_code=401, detail="Invalid verification code.")

        user = db.query(User).filter_by(email=email).first()
        if not user:
            logger.warning(f"[Verify ❌] No user found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found.")

        if user.is_verified:
            logger.info(f"[Verify ✅] Already verified: {email}")
            return {"status": "ok", "message": "Email already verified."}

        # Update verification flag
        user.is_verified = True
        db.commit()
        redis_client.delete(redis_key)

        logger.info(f"[Verify ✅] Email verified successfully: {email}")
        return {"status": "ok", "message": "Email verified successfully."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Verify ❌] Internal error for {email}: {e}")
        raise HTTPException(status_code=500, detail="Verification failed. Please try again later.")



