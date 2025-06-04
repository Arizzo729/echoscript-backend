from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_user_by_email, update_user_password
from app.auth.auth_utils import hash_password
from app.config import redis_client

router = APIRouter()

class VerifyReset(BaseModel):
    email: EmailStr
    code: str
    new_password: str

@router.post("/api/auth/verify-reset")
async def verify_reset(data: VerifyReset):
    saved_code = redis_client.get(f"reset:{data.email}")
    if not saved_code or saved_code.decode() != data.code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    hashed = hash_password(data.new_password)
    update_user_password(data.email, hashed)
    redis_client.delete(f"reset:{data.email}")
    return {"status": "ok"}
