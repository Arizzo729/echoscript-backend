# routes/register.py — EchoScript.AI Secure User Registration

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.models import User
from app.db import get_db
from app.auth_utils import hash_password, create_access_token
from app.utils.logger import logger  # optional logging

router = APIRouter(prefix="/auth", tags=["Authentication"])

# === Request Model ===

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

# === Register Endpoint ===

@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        new_user = User(
            email=data.email,
            password=hash_password(data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token({"sub": new_user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": new_user.email,
                "id": new_user.id,
                "name": new_user.email.split("@")[0].title(),
                "plan": "free"
            }
        }

    except Exception as e:
        logger.error(f"[Register] Failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
