from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from app.config import redis_client
from app.utils.send_email import send_email

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


# === Request Model ===
class NewsletterSubscription(BaseModel):
    email: EmailStr


# === Route: Subscribe to Newsletter ===
@router.post("/subscribe")
async def subscribe_to_newsletter(data: NewsletterSubscription, request: Request):
    email = data.email
    key = f"newsletter:{email}"

    # Prevent duplicate subscriptions
    if redis_client.get(key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already subscribed.",
        )

    try:
        redis_client.set(key, "subscribed")
        send_email(
            to_email=email,
            subject="Welcome to EchoScript.AI!",
            body="Thanks for subscribing to our newsletter. You'll receive updates soon!",
        )
        return {"status": "ok", "message": "Subscription successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}")
