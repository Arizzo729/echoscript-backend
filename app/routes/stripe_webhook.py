from __future__ import annotations

import logging
from typing import Any, Dict

import stripe  # type: ignore[attr-defined]
from fastapi import APIRouter, HTTPException, Request

from app.config import config
from app.utils.stripe_client import sync_subscription_from_stripe

router = APIRouter(prefix="/api/stripe", tags=["Stripe Webhook"])
logger = logging.getLogger(__name__)
WEBHOOK_SECRET: str = config.STRIPE_WEBHOOK_SECRET


@router.post("/webhook")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        if not WEBHOOK_SECRET:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
        event = stripe.Webhook.construct_event(  # type: ignore[attr-defined]
            payload=payload,
            sig_header=sig_header,
            secret=WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Webhook verification failed")

    event_type = event.get("type", "")
    try:
        if event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            # pass FULL event (sync expects it)
            sync_subscription_from_stripe(event)

        elif event_type == "checkout.session.completed":
            # be defensive: fetch the subscription & wrap like an event object
            session_obj = event.get("data", {}).get("object", {})
            sub_id = session_obj.get("subscription")
            if sub_id:
                sub = stripe.Subscription.retrieve(sub_id)  # type: ignore[attr-defined]
                sync_subscription_from_stripe({"data": {"object": sub}})
    except Exception as e:
        logger.error(f"Error handling Stripe event {event_type}: {e}")

    return {"received": True}
