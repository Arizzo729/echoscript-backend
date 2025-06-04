# app/routes/user.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth.auth_utils import decode_token
from app.db import get_db
from app.models import User

router = APIRouter()

class AvatarUpdateRequest(BaseModel):
    avatar_url: str

@router.post("/api/user/avatar")
def update_avatar(
    data: AvatarUpdateRequest,
    token: str = Depends(decode_token),
    db: Session = Depends(get_db)
):
    if not token or "email" not in token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.email == token["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.avatar = data.avatar_url
    db.commit()

    return {"status": "success", "avatar": user.avatar}
