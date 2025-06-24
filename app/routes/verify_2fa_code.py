from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
from app.config import redis_client
from app.db import get_db
from app.auth_utils import create_access_token
from app.models import User
from app.utils.logger import logger

router = APIRouter(tags=["Authentication"])

class Verify2FARequest(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=12)

@router.post("/api/auth/verify-2fa-code", response_model=dict)
def verify_2fa_code(data: Verify2FARequest, db: Session = Depends(get_db)):
    if not redis_client:
        logger.error("❌ Redis not connected. Cannot verify 2FA.")
        raise HTTPException(status_code=500, detail="Internal server error.")

    redis_key = f"2fa:{data.email}"
    stored_code = redis_client.get(redis_key)

    if not stored_code:
        logger.warning(f"⚠️ 2FA code not found for {data.email}")
        raise HTTPException(status_code=400, detail="2FA code expired or not found.")

    if stored_code.decode("utf-8") != data.code:
        logger.warning(f"❌ Invalid 2FA code for {data.email}")
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        logger.warning(f"❌ User not found for 2FA: {data.email}")
        raise HTTPException(status_code=404, detail="User not found.")

    if hasattr(user, "is_verified") and not user.is_verified:
        logger.warning(f"🚫 Login blocked for unverified user: {data.email}")
        raise HTTPException(status_code=403, detail="Email not verified.")

    # Generate access token
    try:
        access_token = create_access_token({"sub": user.email})
    except Exception as e:
        logger.exception(f"❌ Token creation failed for {data.email}")
        raise HTTPException(status_code=500, detail="Token generation failed.")

    # Cleanup code
    redis_client.delete(redis_key)
    logger.info(f"✅ 2FA verified and token issued for {data.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "plan": user.plan,
            "verified": user.is_verified if hasattr(user, "is_verified") else True
        }
    }

