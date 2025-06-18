from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
from app.config import redis_client
from app.db import get_db
from app.auth_utils import create_access_token
from app.models import User
from app.utils.logger import logger

router = APIRouter()

class Verify2FARequest(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=12)

@router.post("/api/auth/verify-2fa-code")
def verify_2fa_code(data: Verify2FARequest, db: Session = Depends(get_db)):
    redis_key = f"2fa:{data.email}"
    stored_code = redis_client.get(redis_key)

    if not stored_code:
        raise HTTPException(status_code=400, detail="2FA code expired or not found.")

    if stored_code.decode("utf-8") != data.code:
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Optional: block login if not verified
    if hasattr(user, "is_verified") and not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified.")

    access_token = create_access_token({"sub": user.email})

    # Clean up used code
    redis_client.delete(redis_key)

    logger.info(f"✅ 2FA verified: {data.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "id": user.id,
            "plan": user.plan,
            "verified": user.is_verified if hasattr(user, "is_verified") else True
        }
    }
