# routes/password_reset.py — EchoScript.AI Secure Password Reset

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import random
import string
from app.auth_utils import hash_password
from app.utils.logger import logger  # optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory temporary store (swap with DB/Redis later)
reset_tokens = {}
users = {
    "user@example.com": {
        "password": "hashed_pw",
        "verified": True
    }
}

# --- Mock Email Sender ---
def send_email(to: str, subject: str, body: str):
    logger.info(f"[Email] → {to}: {subject}\n{body}")
    # TODO: Replace with actual SendGrid/Mailgun later

# --- Schemas ---

class ResetRequest(BaseModel):
    email: EmailStr

class VerifyReset(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# --- Request Reset Code ---

@router.post("/send-reset-code")
def send_reset_code(data: ResetRequest):
    if data.email not in users:
        raise HTTPException(status_code=404, detail="Email not found")

    code = ''.join(random.choices(string.digits, k=6))
    reset_tokens[data.email] = code

    send_email(
        to=data.email,
        subject="Your EchoScript.AI Reset Code",
        body=f"Your verification code is: {code}"
    )

    return {"status": "code_sent"}

# --- Verify Reset Code & Set New Password ---

@router.post("/verify-reset")
def verify_reset(data: VerifyReset):
    if reset_tokens.get(data.email) != data.code:
        raise HTTPException(status_code=401, detail="Invalid reset code")

    # Replace this with database user update logic
    users[data.email]["password"] = hash_password(data.new_password)

    # Cleanup
    reset_tokens.pop(data.email, None)

    return {"status": "password_reset"}
