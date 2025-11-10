# app/schemas/auth.py
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ----- Auth -----


class LoginRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)


class SignupRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    username: str | None = Field(None)


class SignupResponse(BaseModel):
    id: int = Field(...)
    email: EmailStr = Field(...)
    access_token: str = Field(...)
    token_type: str = Field("bearer")


class Token(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field("bearer")
    refresh_token: str | None = None


class TokenPayload(BaseModel):
    sub: str = Field(...)
    exp: datetime = Field(...)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


# ----- Password reset -----


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(...)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(...)
    new_password: str = Field(..., min_length=8)


class PasswordResetResponse(BaseModel):
    sent: bool = Field(...)


# ----- Email verification -----


class VerifyEmailRequest(BaseModel):
    email: EmailStr = Field(...)


class VerifyEmailResponse(BaseModel):
    verified: bool = Field(...)


__all__ = [
    "LoginRequest",
    "SignupRequest",
    "SignupResponse",
    "Token",
    "TokenPayload",
    "RefreshRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "PasswordResetResponse",
    "VerifyEmailRequest",
    "VerifyEmailResponse",
]
