from fastapi import APIRouter, Request
import stripe
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException

load_dotenv()

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_LOOKUP = {
    "pro": "price_12345",         # Replace with actual Stripe price ID
    "enterprise": "price_67890"   # Replace with actual Stripe price ID
}

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    plan_id = data.get("plan_id", "pro")

    price_id = PRICE_LOOKUP.get(plan_id)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan selected.")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="https://echoscript.ai/success",
        cancel_url="https://echoscript.ai/purchase",
    )

    return {"url": session.url}