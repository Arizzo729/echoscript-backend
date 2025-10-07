# app/routes/paypal.py
import os
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/paypal", tags=["PayPal"])

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_ENV = (os.getenv("PAYPAL_ENV") or "sandbox").lower()

if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
    # Don't crash import; we’ll error at call time with a 400
    pass

BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_ENV == "sandbox" else "https://api-m.paypal.com"

async def _get_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Missing PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET")
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{BASE}/v1/oauth2/token", data="grant_type=client_credentials", headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail=f"PayPal OAuth failed: {r.text}")
        return r.json()["access_token"]

class CreateOrderBody(BaseModel):
    amount: str = "10.00"
    currency: str = "USD"
    intent: str = "CAPTURE"  # or "AUTHORIZE"

@router.post("/create-order")
async def create_order(body: CreateOrderBody):
    token = await _get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "intent": body.intent,
        "purchase_units": [{"amount": {"currency_code": body.currency, "value": body.amount}}],
        "application_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
        },
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{BASE}/v2/checkout/orders", json=payload, headers=headers)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail=f"PayPal create-order failed: {r.text}")
        data = r.json()
        return {"id": data["id"]}

class CaptureOrderBody(BaseModel):
    order_id: str

@router.post("/capture-order")
async def capture_order(body: CaptureOrderBody):
    token = await _get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{BASE}/v2/checkout/orders/{body.order_id}/capture", headers=headers)
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail=f"PayPal capture failed: {r.text}")
        return r.json()
