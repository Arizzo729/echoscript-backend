from fastapi import APIRouter, Request
import stripe, os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    plan_id = data.get("plan_id", "pro")  # fallback

    # Define your product details
    price_lookup = {
        "pro": "price_12345",  # ← Replace with actual price_id from Stripe
        "enterprise": "price_67890"
    }

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",  # or "payment" for one-time
        line_items=[{
            "price": price_lookup[plan_id],
            "quantity": 1,
        }],
        success_url="https://echoscript.ai/success",
        cancel_url="https://echoscript.ai/purchase",
    )
    return {"url": session.url}
