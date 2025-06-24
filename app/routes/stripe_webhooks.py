from fastapi import APIRouter, Request, Header, HTTPException
import stripe
import os
import logging

router = APIRouter(prefix="/webhook", tags=["Stripe Webhook"])

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
        logging.exception("[Webhook ❌] Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logging.exception("[Webhook ❌] Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # === Handle Events ===
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        plan_id = session.get("metadata", {}).get("plan_id", "pro")

        logging.info(f"[Webhook ✅] Payment received for {customer_email} | Plan: {plan_id}")

        # TODO: Integrate actual user upgrade logic
        # Example:
        # user = db.query(User).filter_by(email=customer_email).first()
        # if user:
        #     user.plan = plan_id
        #     db.commit()
        #     logging.info(f"[Upgrade ✅] {customer_email} upgraded to {plan_id}")

    return {"status": "success"}

