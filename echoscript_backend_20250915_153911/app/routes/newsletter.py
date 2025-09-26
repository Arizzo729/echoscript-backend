import logging

from fastapi import APIRouter, HTTPException, status

from app.config import config
from app.schemas.newsletter import (
    NewsletterResponse,
    NewsletterSubscribeRequest,
    NewsletterUnsubscribeRequest,
)
from app.utils.redis_client import delete_key, set_value
from app.utils.send_email import send_email

router = APIRouter()
logger = logging.getLogger("echoscript")


@router.post(
    "/subscribe",
    response_model=NewsletterResponse,
    summary="Subscribe an email to the newsletter",
)
async def subscribe(request: NewsletterSubscribeRequest) -> NewsletterResponse:
    """
    Subscribe an email address to the newsletter list.
    Stores the subscription in Redis and sends a welcome email if configured.
    """
    key = f"newsletter:{request.email}"
    try:
        # Store subscription flag in Redis (no expiration)
        set_value(key, "subscribed")
        # Optionally send a confirmation email
        if config.EMAIL_ADDRESS and config.EMAIL_PASSWORD:
            try:
                send_email(
                    to_address=request.email,
                    subject="Welcome to the EchoScript.AI Newsletter",
                    body="Thank you for subscribing to the EchoScript.AI newsletter!",
                )
            except Exception as e:
                logger.warning(f"Failed to send newsletter welcome email: {e}")
        return NewsletterResponse(status="subscribed")
    except Exception as e:
        logger.error(f"Newsletter subscribe error for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to subscribe to newsletter",
        )


@router.delete(
    "/unsubscribe",
    response_model=NewsletterResponse,
    summary="Unsubscribe an email from the newsletter",
)
async def unsubscribe(request: NewsletterUnsubscribeRequest) -> NewsletterResponse:
    """
    Unsubscribe an email address from the newsletter list.
    Removes the subscription flag from Redis.
    """
    key = f"newsletter:{request.email}"
    try:
        delete_key(key)
        return NewsletterResponse(status="unsubscribed")
    except Exception as e:
        logger.error(f"Newsletter unsubscribe error for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to unsubscribe from newsletter",
        )
