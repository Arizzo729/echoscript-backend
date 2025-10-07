# app/routes/paypal.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/paypal", tags=["paypal"])

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "") or os.getenv("VITE_PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "") or os.getenv("PAYPAL_SECRET", "")
PAYPAL_ENV = (os.getenv("PAYPAL_ENV") or "sandbox").lower()

if PAYPAL_ENV not in {"sandbox", "live", "production"}:
    PAYPAL_ENV = "sandbox"

BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_ENV == "sandbox" else "https://api-m.paypal.com"

class CreateBody(BaseModel):
    amount: str
    currency: str = "USD"
    plan: str | None = None

async def _paypal_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        raise HTTPException(status_code=500, detail="PayPal credentials missing on server.")
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=auth,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"PayPal token error: {r.text}")
        return r.json()["access_token"]

@router.options("/create-order")
async def preflight_create():
    return {}

@router.post("/create-order")
async def create_order(body: CreateBody):
    token = await _paypal_token()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v2/checkout/orders",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {"amount": {"currency_code": body.currency, "value": body.amount}}
                ],
                "application_context": {
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                },
            },
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"PayPal create-order error: {r.text}")
        data = r.json()
        return {"id": data["id"]}

class CaptureBody(BaseModel):
    orderID: str

@router.options("/capture-order")
async def preflight_capture():
    return {}

@router.post("/capture-order")
async def capture_order(body: CaptureBody):
    token = await _paypal_token()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v2/checkout/orders/{body.orderID}/capture",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"PayPal capture error: {r.text}")
        return r.json()
