from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
import uuid
import random

from app.db import get_db
from app.models.user import User
from app.auth_utils import hash_password, verify_password
from app.utils.security import create_access_token
from app.utils.logger import logger
from app.utils.redis_client import redis_client
from app.utils.send_email import send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


# —— Request & Response Schemas —— #
class RegisterRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class VerifyRequest(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# —— Register Endpoint —— #
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True,
        is_admin=False,
        is_verified=False
    )
    db.add(user)
    db.commit()

    code = f"{random.randint(100000, 999999)}"
    redis_client.setex(f"verify:{data.email}", 900, code)
    logger.info(f"[Auth][Register] Verification code sent to {data.email}")

    send_email(
        to=data.email,
        subject="🔐 Verify your EchoScript.AI account",
        content=(
            f"Welcome to EchoScript.AI!\n\n"
            f"Your verification code is: {code}\n"
            "It expires in 15 minutes."
        )
    )

    return {"message": "Registration successful. Check your email for the verification code."}


# —— Email Verification Endpoint —— #
@router.post("/verify", response_model=TokenResponse)
def verify_email(data: VerifyRequest, db: Session = Depends(get_db)):
    key = f"verify:{data.email}"
    stored = redis_client.get(key)
    if not stored or stored.decode() != data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code."
        )

    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.is_verified = True
    db.commit()
    redis_client.delete(key)

    token = create_access_token({"sub": user.id})
    return {"access_token": token}


# —— Login Endpoint —— #
@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified."
        )

    token = create_access_token({"sub": user.id})
    return {"access_token": token}
