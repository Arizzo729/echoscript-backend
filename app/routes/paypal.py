# app/routes/paypal.py

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from base64 import b64encode

PAYPAL_ENV = (os.getenv("PAYPAL_ENV") or "sandbox").lower()  # "sandbox" or "live"
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")

BASE = "https://api-m.paypal.com" if PAYPAL_ENV == "live" else "https://api-m.sandbox.paypal.com"

router = APIRouter(tags=["paypal"])

class CreateOrderBody(BaseModel):
    value: str | None = "10.00"            # USD by default
    description: str | None = "EchoScript purchase"

class CaptureOrderBody(BaseModel):
    orderID: str

async def _get_access_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        raise HTTPException(status_code=500, detail="PayPal keys not configured on server.")
    auth = b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v1/oauth2/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"PayPal token error: {r.text}")
    return r.json()["access_token"]

@router.post("/paypal/create-order")
async def create_order(body: CreateOrderBody):
    token = await _get_access_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": "USD", "value": body.value or "10.00"},
             "description": body.description or "EchoScript purchase"}
        ]
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"PayPal create-order failed: {r.text}")
    data = r.json()
    return {"id": data["id"], "status": data["status"]}

@router.post("/paypal/capture-order")
async def capture_order(body: CaptureOrderBody):
    token = await _get_access_token()
    order_id = body.orderID
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"PayPal capture failed: {r.text}")
    return r.json()

