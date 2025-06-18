# app/routes/stripe_webhook.py
from fastapi import APIRouter, Request, Header, HTTPException
import stripe
import os
import logging

router = APIRouter(prefix="/webhook", tags=["Stripe Webhook"])

# Set your Stripe secret key and webhook secret
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=endpoint_secret
        )
    except ValueError:
        logging.error("Invalid payload.")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logging.error("Invalid signature.")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # --- Handle event types ---
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        plan_id = session.get("metadata", {}).get("plan_id", "pro")

        # TODO: Update your database logic here
        logging.info(f"[Stripe Webhook] ✅ Payment confirmed for {customer_email} | Plan: {plan_id}")

        # Example: mark user as pro and grant minutes
        # await db.mark_user_as_pro(email=customer_email)

    return {"status": "success"}
