from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from uuid import uuid4
import random
from app.models import User
from app.db import get_db
from app.auth_utils import hash_password, create_access_token
from app.utils.logger import logger
from app.utils.send_email import send_email
from app.config import redis_client

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        # Create new user (unverified initially)
        new_user = User(
            id=str(uuid4()),
            email=data.email,
            password=hash_password(data.password),
            is_active=True,
            is_admin=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate and store email verification code
        verification_code = str(random.randint(100000, 999999))
        redis_client.setex(f"verify:{data.email}", 900, verification_code)
        logger.info(f"[Register] Verification code for {data.email} → {verification_code}")

        # Send verification email
        send_email(
            to=data.email,
            subject="EchoScript.AI Email Verification",
            content=f"Welcome to EchoScript.AI!\n\nYour verification code is: {verification_code}\nIt will expire in 15 minutes."
        )

        # Return response with JWT but client should block access until verified
        token = create_access_token({"sub": new_user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": new_user.email,
                "id": new_user.id,
                "verified": False,
                "plan": new_user.plan
            },
            "message": "Account created. Please verify your email."
        }

    except Exception as e:
        logger.error(f"[Register Error] {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
