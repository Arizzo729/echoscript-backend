from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import stripe
import os

load_dotenv()

router = APIRouter()

# 🔐 Load Stripe secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# 🧾 Stripe plan pricing (set in .env)
PLAN_PRICES = {
    "pro": os.getenv("STRIPE_PRO_PRICE_ID"),
    "enterprise": os.getenv("STRIPE_ENTERPRISE_PRICE_ID")  # Optional: Add more plans
}

@router.post("/api/create-checkout-session")
async def create_checkout_session(request: Request):
    try:
        body = await request.json()
        plan = body.get("plan")

        price_id = PLAN_PRICES.get(plan)
        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid or missing plan ID.")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            success_url=os.getenv("STRIPE_SUCCESS_URL", "https://echoscript.ai/success"),
            cancel_url=os.getenv("STRIPE_CANCEL_URL", "https://echoscript.ai/purchase"),
            metadata={"plan": plan},
        )

        return JSONResponse({"url": session.url})

    except stripe.error.StripeError as se:
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(se)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")