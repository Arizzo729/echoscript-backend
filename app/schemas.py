# === app/schemas.py ===

from enum import Enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# -------------------------------------------------------------------
# Shared enums
# -------------------------------------------------------------------
class SubscriptionStatus(str, Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    unpaid = "unpaid"
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"


# -------------------------------------------------------------------
# Item schemas
# -------------------------------------------------------------------
class ItemBase(BaseModel):
    name: str = Field(..., example="My Item")
    description: Optional[str] = Field(None, example="A short description")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated name")
    description: Optional[str] = Field(None, example="Updated description")


class ItemRead(ItemBase):
    id: int

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# User schemas
# -------------------------------------------------------------------
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    is_active: bool = Field(..., example=True)


class UserCreate(UserBase):
    password: str = Field(..., example="strongpassword123")


class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# Subscription schemas
# -------------------------------------------------------------------
class SubscriptionBase(BaseModel):
    plan_name: str = Field(..., example="Pro Plan")
    status: SubscriptionStatus = Field(..., example=SubscriptionStatus.active)


class SubscriptionCreate(BaseModel):
    stripe_subscription_id: str = Field(..., example="sub_ABC123")
    stripe_customer_id: str = Field(..., example="cus_XYZ789")
    plan_name: str = Field(..., example="Pro Plan")


class SubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = Field(
        None, example=SubscriptionStatus.canceled
    )


class SubscriptionRead(SubscriptionBase):
    id: int
    user_id: int
    stripe_subscription_id: str
    stripe_customer_id: str
    started_at: datetime
    renewed_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# Newsletter subscription schemas
# -------------------------------------------------------------------
class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr = Field(..., example="subscriber@example.com")


class NewsletterSubscribeResponse(BaseModel):
    status: str = Field(..., example="subscribed")
    message: Optional[str] = Field(None, example="Thank you for subscribing!")


# -------------------------------------------------------------------
# Aggregated / nested schemas (if you ever need them)
# -------------------------------------------------------------------
class UserWithSubscriptions(UserRead):
    subscriptions: List[SubscriptionRead] = []

    class Config:
        orm_mode = True
