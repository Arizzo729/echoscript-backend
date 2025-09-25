# app/schemas/subscription.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import SubscriptionStatus


class SubscribeRequest(BaseModel):
    """
    Request schema for subscribing to a plan.
    Accepts a dashboard Price ID (legacy) or a plan code.
    """

    # Legacy (some old callers may still send a Price ID)
    plan_id: Optional[str] = Field(
        default=None,
        description="Stripe Price ID (e.g., 'price_123'). Deprecated in favor of 'plan'.",
        json_schema_extra={"example": "price_1Hh1XYZabc123"},
    )
    # Canonical (plan code your checkout route expects)
    plan: Optional[str] = Field(
        default=None,
        description="Plan code: 'pro' | 'premium' | 'edu'",
        json_schema_extra={"example": "pro"},
    )


class CancelRequest(BaseModel):
    """Request schema for canceling a subscription."""

    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for cancellation",
        json_schema_extra={"example": "No longer needed"},
    )


class SubscriptionOut(BaseModel):
    """
    Minimal subscription read model aligned with the ORM.
    """

    id: int = Field(..., description="Internal subscription record ID")
    stripe_subscription_id: Optional[str] = Field(
        default=None, description="Stripe subscription object ID"
    )
    stripe_customer_id: Optional[str] = Field(
        default=None, description="Stripe customer object ID"
    )
    status: SubscriptionStatus = Field(..., description="Current subscription status")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last-updated timestamp")

    model_config = ConfigDict(from_attributes=True)


# --- Backwards compatibility for older imports ---
class SubscriptionRead(SubscriptionOut):
    """Alias model kept for backward compatibility with older imports."""

    pass


__all__ = [
    "SubscribeRequest",
    "CancelRequest",
    "SubscriptionOut",
    "SubscriptionRead",  # <- legacy name expected by app/schemas/user.py
]
