# app/schemas/auth.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Schema for user login request.
    """

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")


class SignupRequest(BaseModel):
    """
    Schema for user signup/registration request.
    """

    email: EmailStr = Field(..., description="New user's email address")
    password: str = Field(..., min_length=8, description="New user's password")


class Token(BaseModel):
    """
    Access & refresh token response schema.
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type, typically 'bearer'")
    refresh_token: Optional[str] = Field(
        None, description="JWT refresh token, if issued"
    )


class TokenPayload(BaseModel):
    """
    Data stored in the JWT payload.
    """

    sub: str = Field(..., description="Subject (user ID) stored in token")
    exp: datetime = Field(..., description="Expiration timestamp of the token")


class RefreshRequest(BaseModel):
    """
    Schema for token refresh request.
    """

    refresh_token: Optional[str] = Field(
        None, description="Refresh token to obtain a new access token"
    )


__all__ = [
    "LoginRequest",
    "SignupRequest",
    "Token",
    "TokenPayload",
    "RefreshRequest",
]
