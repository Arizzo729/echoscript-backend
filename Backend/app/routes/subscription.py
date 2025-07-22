from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Subscription, SubscriptionStatus
from app.schemas.subscription import (CancelRequest, SubscribeRequest,
                                      SubscriptionOut)
from app.utils.logger import logger
from app.utils.stripe_client import (cancel_stripe_subscription,
                                     create_stripe_checkout_session)

router = APIRouter()


@router.get(
    "/me",
    response_model=SubscriptionOut,
    summary="Retrieve current user's subscription details",
)
async def get_subscription(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> SubscriptionOut:
    """
    Fetches the most recent subscription for the current user.
    """
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.started_at.desc())
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for user",
        )
    return SubscriptionOut.from_orm(sub)


@router.post(
    "/checkout-session",
    response_model=Dict[str, str],
    summary="Create a Stripe Checkout session for subscribing",
)
async def create_checkout_session(
    request: SubscribeRequest, current_user=Depends(get_current_user)
) -> Dict[str, str]:
    """
    Creates a Stripe checkout URL for the given plan.
    """
    try:
        url = create_stripe_checkout_session(
            user_id=current_user.id,
            price_id=request.plan_id,
        )
        return {"url": url}
    except HTTPException:
        # Already properly formatted HTTPException from stripe_client
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create checkout session",
        )


@router.post(
    "/cancel",
    response_model=SubscriptionOut,
    summary="Cancel the user's active subscription",
)
async def cancel_subscription(
    request: CancelRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubscriptionOut:
    """
    Cancels the user's latest active subscription immediately.
    """
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status == SubscriptionStatus.active,
        )
        .order_by(Subscription.started_at.desc())
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active subscription not found",
        )

    try:
        # cast to str so mypy sees the correct type
        cancel_stripe_subscription(str(sub.stripe_subscription_id))

        # Update ORM columns
        sub.status = SubscriptionStatus.canceled  # type: ignore[assignment]
        sub.canceled_at = datetime.utcnow()  # type: ignore[assignment]

        db.commit()
        db.refresh(sub)
        return SubscriptionOut.from_orm(sub)
    except HTTPException:
        # Already proper HTTPException from stripe_client
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to cancel subscription",
        )


__all__ = ["get_subscription", "create_checkout_session", "cancel_subscription"]
