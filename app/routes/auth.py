from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.models import User
from app.db import get_db
from app.auth_utils import hash_password, create_access_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(email=data.email, password=hash_password(data.password))
    db.add(new_user)
    db.commit()

    token = create_access_token({"email": data.email})
    return {"access_token": token}
