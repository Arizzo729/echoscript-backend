# paypal.py
import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

PAYPAL_ENV = os.getenv("PAYPAL_ENV", "sandbox").lower().strip()  # "sandbox" or "live"
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_ENV != "live" else "https://api-m.paypal.com"

router = APIRouter(prefix="/api/paypal", tags=["paypal"])

async def _get_access_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Missing PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET on server")

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{BASE}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"PayPal token error: {resp.text}")
        data = resp.json()
        return data["access_token"]

@router.get("/health")
async def paypal_health():
    return {
        "ok": True,
        "env": "live" if PAYPAL_ENV == "live" else "sandbox",
        "has_client_id": bool(PAYPAL_CLIENT_ID),
        "has_client_secret": bool(PAYPAL_CLIENT_SECRET),
        "base": BASE,
    }

@router.post("/create-order")
async def create_order(amount: Optional[str] = "9.99", currency: Optional[str] = "USD", plan: Optional[str] = None):
    access_token = await _get_access_token()

    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": currency, "value": amount}, "custom_id": plan or "generic"}
        ],
        "application_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
            # Optional: set return/cancel URLs if you use redirect flow instead of JS SDK approval
        },
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=body,
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=resp.status_code, detail=f"create-order failed: {resp.text}")
        data = resp.json()
        # Return at least the order id for the JS SDK onApprove
        return {"id": data.get("id"), "status": data.get("status"), "links": data.get("links")}

@router.post("/capture-order/{order_id}")
async def capture_order(order_id: str):
    access_token = await _get_access_token()
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=resp.status_code, detail=f"capture failed: {resp.text}")
        return resp.json()

