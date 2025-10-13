# app/routes/signup.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import SignupRequest, SignupResponse
from app.utils.auth_utils import hash_password

# Use the same prefix family as login/refresh
router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup", response_model=SignupResponse, summary="Create a new account")
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user = User(email=payload.email, password=hash_password(payload.password))  # type: ignore[arg-type]
    db.add(user)
    db.commit()
    db.refresh(user)
    return SignupResponse(id=user.id, email=user.email)
