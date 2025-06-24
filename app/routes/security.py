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

# === Helper: Get Authenticated User from JWT ===
def get_authenticated_user(authorization: str, db: Session) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]
    token_data = decode_token(token)
    if not token_data or "sub" not in token_data:
        raise HTTPException(status_code=401, detail="Token verification failed.")

    user = db.query(User).filter_by(email=token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return user

# === GET: 2FA Status ===
@router.get("/2fa-status")
def get_2fa_status(
    authorization: str = Header(..., description="Bearer access token"),
    db: Session = Depends(get_db)
):
    try:
        user = get_authenticated_user(authorization, db)
        return {
            "status": "success",
            "enabled": bool(getattr(user, "two_factor_enabled", False)),
            "email": user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[2FA Status ❌] Internal server error: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve 2FA status.")

# === POST: Enable or Disable 2FA ===
@router.post("/2fa-toggle")
def toggle_2fa(
    data: TwoFAUpdate,
    authorization: str = Header(..., description="Bearer access token"),
    db: Session = Depends(get_db)
):
    try:
        user = get_authenticated_user(authorization, db)

        if user.two_factor_enabled == data.enable:
            return {
                "status": "noop",
                "message": f"2FA is already {'enabled' if data.enable else 'disabled'}.",
                "enabled": user.two_factor_enabled
            }

        user.two_factor_enabled = data.enable
        db.commit()

        logger.info(f"[2FA Toggle ✅] {user.email} → {'ENABLED' if data.enable else 'DISABLED'}")
        return {
            "status": "success",
            "message": f"2FA {'enabled' if data.enable else 'disabled'} successfully.",
            "enabled": data.enable
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[2FA Toggle ❌] Internal error for {authorization}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update 2FA setting.")


