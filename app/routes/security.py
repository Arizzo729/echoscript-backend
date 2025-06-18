# app/routes/security/2fa.py — EchoScript.AI 2FA Toggle API

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.auth_utils import decode_token
from app.utils.logger import logger

router = APIRouter(prefix="/api/security", tags=["Security"])

# === Request Schema ===
class TwoFAUpdate(BaseModel):
    enable: bool

# === Get 2FA Status ===
@router.get("/2fa-status")
def get_2fa_status(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token.")

        token = decode_token(authorization.split(" ")[1])
        if not token or "sub" not in token:
            raise HTTPException(status_code=401, detail="Invalid token.")

        user = db.query(User).filter_by(email=token["sub"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        return {"enabled": user.enable_2fa if hasattr(user, "enable_2fa") else False}
    except Exception as e:
        logger.error(f"[2FA Status] Error: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve 2FA status.")

# === Toggle 2FA ===
@router.post("/2fa-toggle")
def toggle_2fa(
    data: TwoFAUpdate,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token.")

        token = decode_token(authorization.split(" ")[1])
        if not token or "sub" not in token:
            raise HTTPException(status_code=401, detail="Invalid token.")

        user = db.query(User).filter_by(email=token["sub"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        user.enable_2fa = data.enable
        db.commit()
        logger.info(f"[2FA] User {user.email} → 2FA {'ENABLED' if data.enable else 'DISABLED'}")

        return {"status": "success", "enabled": data.enable}
    except Exception as e:
        logger.error(f"[2FA Toggle] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update 2FA setting.")

