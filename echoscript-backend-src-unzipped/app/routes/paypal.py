# app/routes/paypal.py
import httpx
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.core.settings import settings

router = APIRouter(prefix="/paypal", tags=["PayPal"])

def get_paypal_base_url() -> str:
    """Returns the base URL for the PayPal API based on the environment."""
    return (
        "https://api-m.sandbox.paypal.com"
        if settings.PAYPAL_ENV == "sandbox"
        else "https://api-m.paypal.com"
    )

async def get_paypal_access_token() -> str:
    """Retrieves an OAuth2 access token from PayPal."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, detail="PayPal client ID or secret is not configured."
        )

    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    url = f"{get_paypal_base_url()}/v1/oauth2/token"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, auth=auth, data=data)
            resp.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            return resp.json()["access_token"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=f"PayPal token error: {e.response.text}"
            )

@router.post("/create-order")
async def create_paypal_order(
    amount: str = "9.99", currency: str = "USD", plan: Optional[str] = None
):
    """Creates a new order in PayPal."""
    access_token = await get_paypal_access_token()
    url = f"{get_paypal_base_url()}/v2/checkout/orders"
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": currency, "value": amount},
                "custom_id": plan or "default_plan",
            }
        ],
        "application_context": {"shipping_preference": "NO_SHIPPING"},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=f"PayPal order creation failed: {e.response.text}"
            )

@router.post("/capture-order/{order_id}")
async def capture_paypal_order(order_id: str):
    """Captures a previously created PayPal order."""
    access_token = await get_paypal_access_token()
    url = f"{get_paypal_base_url()}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=f"PayPal order capture failed: {e.response.text}"
            )