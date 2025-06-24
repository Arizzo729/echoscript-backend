# ✅ EchoScript.AI — Stripe Checkout Session Route (FastAPI)

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import stripe
import os

load_dotenv()

router = APIRouter()

# 🔐 Load secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# 🧾 Define product prices (linked to Stripe dashboard price IDs)
PLAN_PRICES = {
    "pro": os.getenv("STRIPE_PRO_PRICE_ID"),  # e.g. price_1N9xyz...
    # Add more plans as needed
}

@router.post("/api/create-checkout-session")
async def create_checkout_session(request: Request):
    try:
        body = await request.json()
        plan = body.get("plan")

        if not plan or plan not in PLAN_PRICES:
            raise HTTPException(status_code=400, detail="Invalid plan.")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": PLAN_PRICES[plan],
                    "quantity": 1,
                }
            ],
            success_url=os.getenv("STRIPE_SUCCESS_URL", "https://echoscript.ai/success"),
            cancel_url=os.getenv("STRIPE_CANCEL_URL", "https://echoscript.ai/purchase"),
            metadata={"plan": plan},
        )

        return JSONResponse({"url": checkout_session.url})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
