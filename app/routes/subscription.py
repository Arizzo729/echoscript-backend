# 5. app/routes/subscription.py (corrected)

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl, constr
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Subscription, SubscriptionStatus
from app.schemas import SubscriptionRead
from app.utils.stripe_client import (
    create_stripe_checkout_session,
    cancel_stripe_subscription,
)

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


class SubscribeRequest(BaseModel):
    plan_id: constr(min_length=1) = Field(
        ...,
        example="price_1Hh1XYZabc123",
        description="Stripe Price ID for the plan",
    )


class CancelRequest(BaseModel):
    reason: Optional[str] = Field(
        None, example="No longer needed", description="Optional reason for cancellation"
    )


class CheckoutSessionResponse(BaseModel):
    url: HttpUrl = Field(..., description="URL to redirect the user to Stripe Checkout")


class CancelResponse(BaseModel):
    status: SubscriptionStatus = Field(..., description="New subscription status")
    reason: Optional[str] = Field(None, description="Cancellation reason provided by the user")


@router.get(
    "/me",
    response_model=SubscriptionRead,
    summary="Get current user's subscription",
    responses={404: {"description": "No active subscription found"}},
)
def get_my_subscription(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the most recent active subscription for the current user.
    """
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status == SubscriptionStatus.active
        )
        .order_by(Subscription.started_at.desc())
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found for this user.",
        )
    return sub


@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    summary="Create a Stripe Checkout session for a plan",
    status_code=status.HTTP_201_CREATED,
    responses={500: {"description": "Failed to create checkout session"}},
)
def create_checkout_session(
    data: SubscribeRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        session_url = create_stripe_checkout_session(
            user=current_user,
            price_id=data.plan_id,
            db=db,
        )
        return CheckoutSessionResponse(url=session_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Checkout error: {e}",
        )


@router.post(
    "/cancel",
    response_model=CancelResponse,
    summary="Cancel the current user's subscription",
    responses={
        404: {"description": "No active subscription found to cancel"},
        500: {"description": "Cancellation failed"},
    },
)
def cancel_subscription(
    data: CancelRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel the current user's active subscription both in Stripe and locally.
    """
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status == SubscriptionStatus.active
        )
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found to cancel.",
        )

    try:
        cancel_stripe_subscription(sub.stripe_subscription_id)
        sub.status = SubscriptionStatus.canceled
        sub.canceled_at = datetime.utcnow()
        db.commit()
        return CancelResponse(status=sub.status, reason=data.reason)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cancellation failed: {e}",
        )
