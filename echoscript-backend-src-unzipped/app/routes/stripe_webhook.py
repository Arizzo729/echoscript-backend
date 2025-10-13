# app/routes/stripe_webhook.py
import logging
import stripe
from fastapi import APIRouter, Header, Request, HTTPException

from app.core.settings import settings

log = logging.getLogger("stripe.webhook")
router = APIRouter(prefix="/stripe-webhook", tags=["Stripe"])

@router.post("/")
async def stripe_webhook_handler(request: Request, stripe_signature: str = Header(None)):
    """
    Handles incoming webhooks from Stripe.

    - Verifies the webhook signature to ensure it came from Stripe.
    - Processes the event (e.g., `checkout.session.completed`).
    - For now, it just logs the event type.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook secret is not configured.")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured.")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e: # Invalid payload
        log.warning(f"Webhook payload error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e: # Invalid signature
        log.warning(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        log.info(f"Checkout session completed: {session['id']}")
        # Here you would typically fulfill the order, e.g., by creating a subscription
        # in your database, using the metadata to link it to a user.
        # user_id = session.get('metadata', {}).get('user_id')
        # if user_id:
        #     # ... create subscription for user_id ...

    else:
        log.info(f"Unhandled Stripe event type: {event['type']}")

    return {"received": True}