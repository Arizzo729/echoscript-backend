from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import User
from app.auth_utils import hash_password, create_access_token

router = APIRouter()

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed = hash_password(data.password)
    new_user = User(email=data.email, password=hashed)
    db.add(new_user)
    db.commit()

    token = create_access_token({"email": data.email})
    return {"access_token": token}
