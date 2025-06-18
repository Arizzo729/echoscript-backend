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

# === Helper: Get user from token ===
def get_authenticated_user(authorization: str, db: Session) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")

    token_data = decode_token(authorization.split(" ")[1])
    if not token_data or "sub" not in token_data:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user = db.query(User).filter_by(email=token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# === GET: 2FA Status ===
@router.get("/2fa-status")
def get_2fa_status(
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
):
    try:
        user = get_authenticated_user(authorization, db)
        enabled = getattr(user, "two_factor_enabled", False)
        return {"enabled": enabled}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[2FA Status ❌] Internal error: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve 2FA status.")

# === POST: Toggle 2FA ===
@router.post("/2fa-toggle")
def toggle_2fa(
    data: TwoFAUpdate,
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
):
    try:
        user = get_authenticated_user(authorization, db)
        user.two_factor_enabled = data.enable
        db.commit()

        logger.info(f"[2FA Toggle ✅] {user.email} → {'ENABLED' if data.enable else 'DISABLED'}")
        return {"status": "success", "enabled": data.enable}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[2FA Toggle ❌] Internal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update 2FA setting.")


