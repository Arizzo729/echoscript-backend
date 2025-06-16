# app/routes/security/2fa.py — EchoScript.AI 2FA Toggle API

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/api/security", tags=["Security"])

# ⚠️ TEMP: In-memory user 2FA toggle map (use DB/session in production)
user_2fa_store = {
    "default": False  # Replace with per-user entry in production
}

class TwoFAUpdate(BaseModel):
    user_id: str = "default"
    enable: bool

# === Get Current 2FA Status ===
@router.get("/2fa-status")
async def get_2fa_status(user_id: str = "default"):
    enabled = user_2fa_store.get(user_id, False)
    return {"enabled": enabled}

# === Enable/Disable 2FA ===
@router.post("/2fa-toggle")
async def toggle_2fa(update: TwoFAUpdate):
    try:
        user_2fa_store[update.user_id] = update.enable
        # TODO: Integrate with auth/session store for real persistence
        return {
            "status": "success",
            "enabled": update.enable
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="2FA update failed.")
