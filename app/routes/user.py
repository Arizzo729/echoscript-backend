from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from app.auth.auth_utils import decode_token
from app.db import get_db
from app.models import User
from app.utils.logger import logger

router = APIRouter(prefix="/api/user", tags=["User"])

# === Schema ===
class AvatarUpdateRequest(BaseModel):
    avatar_url: HttpUrl

# === Avatar Update Endpoint ===
@router.post("/avatar", response_model=dict)
def update_avatar(
    data: AvatarUpdateRequest,
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
):
    if not authorization.startswith("Bearer "):
        logger.warning("🚫 Missing or invalid auth header.")
        raise HTTPException(status_code=401, detail="Missing or invalid token.")

    try:
        token_str = authorization.split(" ")[1]
        token_data = decode_token(token_str)

        if not token_data or "sub" not in token_data:
            logger.warning("🚫 Token decode failed or malformed.")
            raise HTTPException(status_code=401, detail="Invalid token.")

        user = db.query(User).filter(User.email == token_data["sub"]).first()
        if not user:
            logger.warning(f"🚫 User not found for email: {token_data['sub']}")
            raise HTTPException(status_code=404, detail="User not found.")

        if not getattr(user, "is_verified", False):
            logger.warning(f"🚫 Unverified user: {user.email}")
            raise HTTPException(status_code=403, detail="Email not verified.")

        user.avatar = data.avatar_url
        db.commit()

        logger.info(f"✅ Avatar updated for {user.email}")
        return {"status": "success", "avatar": user.avatar}

    except Exception as e:
        logger.error(f"❌ Avatar update failed: {e}")
        raise HTTPException(status_code=500, detail="Avatar update failed.")

