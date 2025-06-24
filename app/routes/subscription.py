from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import stripe
import os

from app.models.user import User
from app.models.subscription import Subscription
from app.auth_utils import get_current_user
from app.dependencies import get_db

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(
    prefix="/api/subscription",
    tags=["Subscription"],
)

class SubscriptionCreate(BaseModel):
    plan_id: str
    success_url: str
    cancel_url: str

@router.post("/create-session", status_code=status.HTTP_201_CREATED)
def create_checkout_session(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=current_user.email,
            line_items=[{"price": data.plan_id, "quantity": 1}],
            mode="subscription",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={"user_id": current_user.id},
        )
        return {"session_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=getattr(e, "http_status", 500),
            detail=getattr(e, "user_message", str(e)),
        )

@router.get("/status")
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(Subscription).filter_by(user_id=current_user.id).first()
    if not sub:
        return {"active": False, "plan": None}
    return {
        "active": sub.status == "active",
        "plan": sub.plan_id,
        "status": sub.status,
        "stripe_id": sub.stripe_subscription_id,
    }

@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(Subscription).filter_by(user_id=current_user.id).first()
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(
            status_code=404,
            detail="No active subscription to cancel"
        )

    try:
        stripe.Subscription.delete(sub.stripe_subscription_id)
        sub.status = "canceled"
        db.commit()
        return {"success": True, "message": "Subscription canceled"}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=getattr(e, "http_status", 500),
            detail=getattr(e, "user_message", str(e)),
        )
