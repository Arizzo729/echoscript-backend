# app/routes/stripe_webhook.py
import os
import logging
from fastapi import APIRouter, Header, Request, HTTPException

import stripe

log = logging.getLogger("stripe.webhook")

router = APIRouter(prefix="/api/stripe", tags=["stripe-webhook"])

STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET") or ""
stripe.api_key = STRIPE_SECRET
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET") or ""

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET not set on server")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=WEBHOOK_SECRET,
        )
    except Exception as e:
        log.warning("Webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    log.info("Stripe event received: %s", event.get("type"))
    return {"received": True}
