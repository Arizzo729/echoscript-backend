# routes/auth/signup.py — EchoScript.AI Signup Route

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import User
from app.auth_utils import hash_password, create_access_token
from app.utils.logger import logger

router = APIRouter()

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            logger.info(f"[Signup] Attempted re-register: {data.email}")
            raise HTTPException(status_code=400, detail="Email already registered.")

        # Create and store new user
        hashed = hash_password(data.password)
        new_user = User(email=data.email, password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[Signup] New user registered: {data.email}")

        # Generate access token
        token = create_access_token({"sub": data.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": data.email,
                "name": data.email.split("@")[0].title(),
                "plan": "free"
            }
        }

    except Exception as e:
        logger.error(f"[Signup Error] {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")
