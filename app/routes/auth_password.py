from fastapi import APIRouter
from pydantic import BaseModel
import random
import string

router = APIRouter()

# Fake store for demo
reset_tokens = {}  # { email: code }
users = {
    "user@example.com": {
        "password": "hashed_pw",
        "verified": True
    }
}

def send_email(to, subject, body):
    print(f"Sending to {to} - {subject}\n{body}")

class ResetRequest(BaseModel):
    email: str

class VerifyReset(BaseModel):
    email: str
    code: str
    new_password: str

@router.post("/api/auth/send-reset-code")
def send_reset_code(data: ResetRequest):
    if data.email not in users:
        return {"error": "Email not found"}
    code = ''.join(random.choices(string.digits, k=6))
    reset_tokens[data.email] = code
    send_email(data.email, "Your EchoScript Reset Code", f"Your code: {code}")
    return {"status": "ok"}

@router.post("/api/auth/verify-reset")
def verify_reset(data: VerifyReset):
    if reset_tokens.get(data.email) != data.code:
        return {"error": "Invalid code"}
    users[data.email]["password"] = data.new_password  # hash in production!
    del reset_tokens[data.email]
    return {"status": "ok"}
