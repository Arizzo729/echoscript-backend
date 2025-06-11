# ---- EchoScript.AI: routes/user.py ----

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
    if not authorization.startswith("Bearer "):
        logger.warning("🚫 Missing or invalid auth header.")
        raise HTTPException(status_code=401, detail="Missing or invalid token.")

    token_str = authorization.split(" ")[1]
    token = decode_token(token_str)

    if not token or "sub" not in token:
        logger.warning("🚫 Token decode failed or email not found in token.")
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.email == token["sub"]).first()
    if not user:
        logger.warning(f"🚫 User not found for email: {token['sub']}")
        raise HTTPException(status_code=404, detail="User not found")

    user.avatar = data.avatar_url
    db.commit()

    logger.info(f"🖼️ Avatar updated for {user.email}")
    return {"status": "success", "avatar": user.avatar}
