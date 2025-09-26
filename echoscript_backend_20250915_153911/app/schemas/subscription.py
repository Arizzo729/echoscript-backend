from datetime import datetime

from pydantic import BaseModel, Field

from app.models import SubscriptionStatus


class SubscribeRequest(BaseModel):
    """
    Request schema for subscribing to a plan.
    """

    plan_id: str = Field(
        default=...,
        min_length=1,
        description="Stripe Price ID for the plan",
        json_schema_extra={"example": "price_1Hh1XYZabc123"},
    )


class CancelRequest(BaseModel):
    """
    Request schema for canceling a subscription.
    """

    reason: str | None = Field(
        default=None,
        description="Optional reason for cancellation",
        json_schema_extra={"example": "No longer needed"},
    )


class SubscriptionRead(BaseModel):
    id: int
    user_id: int
    plan: str
    status: str
    start_date: datetime
    end_date: datetime

    model_config = {"from_attributes": True}


class SubscriptionOut(BaseModel):
    """
    Response schema for subscription details.
    """

    id: int = Field(default=..., description="Internal subscription record ID")
    stripe_subscription_id: str = Field(
        default=..., description="Stripe subscription object ID"
    )
    stripe_customer_id: str = Field(
        default=..., description="Stripe customer object ID"
    )
    plan_name: str = Field(default=..., description="Name of the subscribed plan")
    status: SubscriptionStatus = Field(
        default=..., description="Current subscription status"
    )
    started_at: datetime = Field(
        default=..., description="Timestamp when subscription started"
    )
    renewed_at: datetime | None = Field(
        default=None, description="Timestamp of last renewal, if any"
    )
    canceled_at: datetime | None = Field(
        default=None, description="Timestamp when subscription was canceled, if any"
    )

    model_config = {"from_attributes": True}


__all__ = [
    "SubscribeRequest",
    "CancelRequest",
    "SubscriptionRead",
    "SubscriptionOut",
]
