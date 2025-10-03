from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class SignupIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
def signup(body: SignupIn):
    # TODO: save user & hash password
    return {"ok": True, "created": True, "email": body.email}

@router.post("/login")
def login(body: LoginIn):
    # TODO: verify and return real JWT
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"ok": True, "access_token": "dummy-token", "token_type": "bearer"}
