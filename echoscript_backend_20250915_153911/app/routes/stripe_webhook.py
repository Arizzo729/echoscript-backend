import logging
from typing import Any

import stripe  # type: ignore[attr-defined]
from fastapi import APIRouter, HTTPException, Request, status

from app.config import config
from app.utils.stripe_client import sync_subscription_from_stripe

router = APIRouter()
logger = logging.getLogger(__name__)

WEBHOOK_SECRET: str = config.STRIPE_WEBHOOK_SECRET


@router.post(
    "/webhook",
    include_in_schema=False,
    summary="Stripe webhook endpoint (hidden from OpenAPI schema)",
)
async def stripe_webhook(request: Request) -> dict[str, str]:
    """
    Verify Stripe signature and process subscription lifecycle events.
    Now also handles checkout.session.completed by fetching the subscription.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    if not WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    try:
        event: dict[str, Any] = stripe.Webhook.construct_event(
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

    event_type = event.get("type", "")

    # Handle subscription lifecycle directly
    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        try:
            sync_subscription_from_stripe(event)
            logger.info(f"Processed Stripe event: {event_type}")
        except Exception as e:
            logger.error(f"Error syncing subscription from Stripe: {e}")
        return {"status": "success"}

    # Handle checkout completion by looking up the subscription
    if event_type == "checkout.session.completed":
        try:
            session_obj = event.get("data", {}).get("object", {}) or {}
            subscription_id = session_obj.get("subscription")
            if subscription_id:
                # Retrieve the latest subscription from Stripe
                subscription = stripe.Subscription.retrieve(subscription_id)
                # Reuse existing sync helper by faking the expected event shape
                fake_event = {
                    "type": "customer.subscription.updated",
                    "data": {"object": subscription},
                }
                sync_subscription_from_stripe(fake_event)
                logger.info("Processed subscription via checkout.session.completed")
            else:
                logger.info(
                    "checkout.session.completed without a subscription id (one-time payment?)"
                )
        except Exception as e:
            logger.error(f"Error handling checkout.session.completed: {e}")
        return {"status": "success"}

    logger.debug(f"Ignoring Stripe event type: {event_type}")
    return {"status": "success"}
