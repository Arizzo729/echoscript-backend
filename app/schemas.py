# === app/schemas.py — Pydantic Schemas ===

from pydantic import BaseModel, EmailStr, constr
from typing import Optional


# === User Schemas ===
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


# === Authentication ===
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# === Utility Schemas ===
class Message(BaseModel):
    detail: str
