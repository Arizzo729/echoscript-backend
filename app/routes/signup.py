# === routes/auth/signup.py — EchoScript.AI User Signup & Email Verification ===

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import User
from app.auth_utils import hash_password
from app.utils.logger import logger
from app.utils.send_email import send_email
from app.config import redis_client

import random
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["Authentication"])

# === Request Schema ===
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

# === Signup Route ===
@router.post("/signup")
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    try:
        # Check for existing account
        if db.query(User).filter(User.email == data.email).first():
            logger.info(f"[Signup] Duplicate registration attempt: {data.email}")
            raise HTTPException(status_code=400, detail="Email already registered.")

        # Create hashed password
        hashed_pw = hash_password(data.password)

        # Initialize user
        new_user = User(
            email=data.email,
            password=hashed_pw,
            is_verified=False,
            is_active=True,
            plan="guest"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[Signup] ✅ Registered: {data.email}")

        # Generate verification code (6-digit numeric)
        try:
            code = str(random.randint(100000, 999999))
        except Exception:
            code = uuid4().hex[:6]

        redis_key = f"verify:{data.email}"
        redis_result = redis_client.setex(redis_key, 900, code)
        if not redis_result:
            logger.error(f"[Redis] ❌ Failed to cache verification code for {data.email}")
            raise HTTPException(status_code=500, detail="Internal error. Try again shortly.")

        logger.info(f"[Verify] Code for {data.email} → {code}")

        # Email the code
        subject = "Verify Your EchoScript.AI Account"
        content = f"""Hello,

Welcome to EchoScript.AI! Your verification code is: {code}

This code is valid for 15 minutes.

Thanks,
EchoScript.AI Team"""

        email_result = send_email(to=data.email, subject=subject, content=content)
        if email_result.get("status") != "success":
            raise Exception(email_result.get("message", "Failed to send email"))

        return {
            "status": "ok",
            "message": "Signup successful. Please check your email to verify your account."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Signup Error] {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")

