# app/routes/signup.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas.auth import SignupRequest, SignupResponse
from app.utils.auth_utils import hash_password
from app.routes.auth import _create_jwt, _set_cookie

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=SignupResponse, summary="Create a new account")
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)) -> SignupResponse:
    # Check if the email is already registered
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Create new user with hashed password
    user = User(email=payload.email, password=hash_password(payload.password))  # type: ignore[arg-type]
    db.add(user)
    db.commit()
    db.refresh(user)
    # Issue a JWT and set cookie for the new user
    token = _create_jwt({"sub": str(user.id), "email": user.email})
    _set_cookie(response, token)
    return SignupResponse(id=user.id, email=user.email)
