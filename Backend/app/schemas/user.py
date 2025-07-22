# app/schemas/user.py

from typing import List

from pydantic import BaseModel, EmailStr, Field

from .subscription import SubscriptionRead


class UserBase(BaseModel):
    """
    Shared user properties.
    """

    email: EmailStr = Field(
        ...,
        json_schema_extra={"example": "user@example.com"},
    )
    is_active: bool = Field(
        ...,
        json_schema_extra={"example": True},
    )


class UserCreate(UserBase):
    """
    Properties to create a new user.
    """

    password: str = Field(
        ...,
        min_length=8,
        json_schema_extra={"example": "strongpassword123"},
    )


class UserRead(UserBase):
    """
    Properties to return for a user.
    """

    id: int

    class Config:
        orm_mode = True


class UserWithSubscriptions(UserRead):
    """
    User with their subscriptions.
    """

    subscriptions: List[SubscriptionRead] = []

    class Config:
        orm_mode = True


__all__ = [
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserWithSubscriptions",
]
