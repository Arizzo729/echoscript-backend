from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.config import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

class VerifyCodeInput(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=12)

@router.post("/verify-email")
def verify_email(data: VerifyCodeInput, db: Session = Depends(get_db)):
    redis_key = f"verify:{data.email}"
    try:
        stored_code = redis_client.get(redis_key)
        if not stored_code:
            raise HTTPException(status_code=400, detail="Verification code expired or not found.")

        if stored_code.decode("utf-8") != data.code:
            raise HTTPException(status_code=401, detail="Invalid verification code.")

        user = db.query(User).filter_by(email=data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        if getattr(user, "is_verified", None) is True:
            logger.info(f"[Verify] Email already verified: {data.email}")
            return {"status": "ok", "message": "Email already verified."}

        user.is_verified = True
        db.commit()

        # Cleanup
        redis_client.delete(redis_key)
        logger.info(f"✅ Email verified: {data.email}")

        return {"status": "ok", "message": "Email verified successfully."}

    except Exception as e:
        logger.error(f"[Verify Error] {e}")
        raise HTTPException(status_code=500, detail="Verification failed. Please try again.")


