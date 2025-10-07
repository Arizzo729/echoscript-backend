# app/routes/paypal.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/paypal", tags=["paypal"])

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
PAYPAL_ENV = (os.getenv("PAYPAL_ENV") or "sandbox").lower()

if PAYPAL_ENV not in {"sandbox", "live"}:
    PAYPAL_ENV = "sandbox"

BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_ENV == "sandbox" else "https://api-m.paypal.com"


async def _paypal_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        raise HTTPException(status_code=500, detail="PayPal not configured on server")
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{BASE}/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"PayPal token error: {r.text}")
        return r.json()["access_token"]


class CreateOrderBody(BaseModel):
    # You can extend this if you want dynamic amounts/plans
    amount: str = "10.00"
    currency: str = "USD"
    description: str | None = "EchoScript purchase"


@router.post("/create-order")
async def create_order(body: CreateOrderBody):
    token = await _paypal_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": body.currency, "value": body.amount},
                "description": body.description or "",
            }
        ],
        "application_context": {
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
            # Optional return/cancel URLs if you ever use redirect flow:
            # "return_url": os.getenv("PAYPAL_RETURN_URL"),
            # "cancel_url": os.getenv("PAYPAL_CANCEL_URL"),
        },
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/v2/checkout/orders",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json=payload,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"PayPal create error: {r.text}")
        data = r.json()
        return {"id": data["id"]}


class CaptureBody(BaseModel):
    orderID: str


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
