# === routes/auth/signup.py — EchoScript.AI Signup & Verification ===

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import User
from app.auth_utils import hash_password
from app.utils.logger import logger
from app.utils.send_email import send_email
from app.config import redis_client
import random, string
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["Authentication"])

# === Request Schema ===
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

# === Signup Endpoint ===
@router.post("/signup")
def signup(data: SignUpRequest, request: Request, db: Session = Depends(get_db)):
    email = data.email.strip().lower()

    # === Duplicate Check ===
    if db.query(User).filter(User.email == email).first():
        logger.info(f"[Signup] Duplicate: {email}")
        raise HTTPException(status_code=400, detail="Email already registered.")

    try:
        # === Create user ===
        hashed_pw = hash_password(data.password)

        new_user = User(
            email=email,
            password=hashed_pw,
            is_verified=False,
            is_active=True,
            plan="guest"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[Signup] ✅ Registered: {email}")

        # === Generate Verification Code ===
        try:
            code = str(random.randint(100000, 999999))
        except Exception:
            code = ''.join(random.choices(string.digits, k=6))

        redis_key = f"verify:{email}"
        if not redis_client.setex(redis_key, 900, code):
            raise RuntimeError("Failed to cache verification code")

        logger.info(f"[Verify] Code sent → {email} ({code})")

        # === Send Email ===
        subject = "Verify Your EchoScript.AI Account"
        content = f"""
Hello 👋,

Thanks for signing up with EchoScript.AI!

Your verification code is: **{code}**

This code will expire in 15 minutes.

If you didn’t create this account, you can ignore this email.

— The EchoScript.AI Team
        """.strip()

        email_status = send_email(to=email, subject=subject, content=content)
        if email_status.get("status") != "success":
            raise RuntimeError(f"Email failed: {email_status.get('message')}")

        return {
            "status": "ok",
            "message": "Signup successful. Check your email for the verification code."
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[Signup Error] {email} — {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")


