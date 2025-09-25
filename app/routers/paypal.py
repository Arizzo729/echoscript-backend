# app/routers/paypal.py
import base64
import os

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/paypal", tags=["paypal"])

ENV = os.getenv("PAYPAL_ENV", "sandbox")
BASE = (
    "https://api-m.sandbox.paypal.com"
    if ENV == "sandbox"
    else "https://api-m.paypal.com"
)
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")


async def _token():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(500, "PayPal credentials missing")
    basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{BASE}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )
        r.raise_for_status()
        return r.json()["access_token"]


@router.post("/create-order")
async def create_order():
    body = {
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": "9.99"}}],
    }
    token = await _token()
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{BASE}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        r.raise_for_status()
        return r.json()  # contains `id` (orderID)


@router.post("/capture-order/{order_id}")
async def capture_order(order_id: str):
    token = await _token()
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{BASE}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
        data = r.json()
        # TODO: verify amount, mark payment as paid in your DB
        return data
