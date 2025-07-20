# === app/schemas/subscription.py ===

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr

from app.models import SubscriptionStatus


class SubscriptionOut(BaseModel):
    """
    Response schema for a user's subscription.
    """
    id: int = Field(..., example=1, description="Subscription record ID")
    user_id: int = Field(..., example=123, description="ID of the user who owns this subscription")
    stripe_subscription_id: constr(min_length=1) = Field(
        ..., example="sub_1ABCDEF...", description="Stripe subscription identifier"
    )
    stripe_customer_id: constr(min_length=1) = Field(
        ..., example="cus_1XYZ123...", description="Stripe customer identifier"
    )
    plan_name: str = Field(..., example="Pro", description="Name of the subscription plan")
    status: SubscriptionStatus = Field(
        ..., example=SubscriptionStatus.active, description="Current status of the subscription"
    )
    started_at: datetime = Field(
        ..., example="2025-07-15T18:00:00Z", description="UTC timestamp when subscription started"
    )
    renewed_at: Optional[datetime] = Field(
        None, example="2025-08-15T18:00:00Z", description="UTC timestamp when subscription was last renewed"
    )
    canceled_at: Optional[datetime] = Field(
        None, example=None, description="UTC timestamp when subscription was canceled, if applicable"
    )

    class Config:
        orm_mode = True
        schema_extra = {
            "description": "Schema for returning subscription details."
        }

