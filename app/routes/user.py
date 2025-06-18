from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from app.auth.auth_utils import decode_token
from app.db import get_db
from app.models import User
from app.utils.logger import logger

router = APIRouter(prefix="/api/user", tags=["User"])

# === Request Schema ===
class AvatarUpdateRequest(BaseModel):
    avatar_url: HttpUrl

# === Avatar Update Endpoint ===
@router.post("/avatar", response_model=dict)
def update_avatar(
    data: AvatarUpdateRequest,
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
):
    # === Validate Authorization Header ===
    if not authorization.lower().startswith("bearer "):
        logger.warning("🚫 Invalid or missing Authorization header.")
        raise HTTPException(status_code=401, detail="Missing or invalid token.")

    token = authorization.split(" ")[1]
    try:
        token_data = decode_token(token)
        user_email = token_data.get("sub")
        if not user_email:
            logger.warning("🚫 Token missing 'sub' claim.")
            raise HTTPException(status_code=401, detail="Invalid token payload.")
    except Exception as e:
        logger.warning(f"❌ Token decoding failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    # === Fetch and Validate User ===
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        logger.warning(f"❌ User not found for email: {user_email}")
        raise HTTPException(status_code=404, detail="User not found.")

    if not getattr(user, "is_verified", False):
        logger.warning(f"🚫 Unverified user attempted avatar update: {user.email}")
        raise HTTPException(status_code=403, detail="Email not verified.")

    # === Update Avatar ===
    try:
        user.avatar = str(data.avatar_url)
        db.commit()
        logger.info(f"✅ Avatar updated for {user.email}")
        return {"status": "success", "avatar": user.avatar}

    except Exception as e:
        db.rollback()
        logger.exception(f"❌ Failed to update avatar for {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Avatar update failed.")


