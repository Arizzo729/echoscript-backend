from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()

# In-memory toggle (replace with DB/user session logic in production)
fake_user_db = {"2fa_enabled": False}

class TwoFAUpdate(BaseModel):
    enable: bool

@router.get("/api/security/2fa-status")
async def get_2fa_status():
    return {"enabled": fake_user_db["2fa_enabled"]}

@router.post("/api/security/2fa-toggle")
async def toggle_2fa(update: TwoFAUpdate):
    fake_user_db["2fa_enabled"] = update.enable
    return {"status": "success", "enabled": update.enable}
