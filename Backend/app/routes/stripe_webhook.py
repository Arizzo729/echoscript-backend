import logging
from typing import Dict

import stripe  # type: ignore[attr-defined]
from fastapi import APIRouter, HTTPException, Request, status

from app.config import config
from app.utils.stripe_client import sync_subscription_from_stripe

router = APIRouter()
logger = logging.getLogger(__name__)

# Stripe webhook endpoint secret (should be set in your environment)
WEBHOOK_SECRET: str = config.STRIPE_WEBHOOK_SECRET


@router.post(
    "/webhook",
    include_in_schema=False,
    summary="Stripe webhook endpoint (hidden from OpenAPI schema)",
)
async def stripe_webhook(request: Request) -> Dict[str, str]:
    """
    Receive Stripe webhook events and synchronize subscription data.

    - Verifies signature using WEBHOOK_SECRET.
    - Processes subscription.created and subscription.updated events.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    try:
        # Verify and construct the event
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=WEBHOOK_SECRET,
        )
    except ValueError:
        logger.warning("Invalid payload in Stripe webhook.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:  # type: ignore[attr-defined]
        logger.warning("Invalid signature in Stripe webhook.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying Stripe webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook verification failed",
        )

    # Only handle subscription lifecycle events
    event_type = event.get("type", "")
    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        try:
            sync_subscription_from_stripe(event)
            logger.info(f"Processed Stripe event: {event_type}")
        except Exception as e:
            # Log errors but do not raise to prevent webhook retries
            logger.error(f"Error syncing subscription from Stripe: {e}")
    else:
        logger.debug(f"Ignoring Stripe event type: {event_type}")

    return {"status": "success"}
