# app/routes/stripe.py
import logging
from fastapi import APIRouter, HTTPException

import stripe
from app.core.settings import settings

log = logging.getLogger("echoscript")
router = APIRouter(prefix="/stripe", tags=["Stripe"])

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

@router.get("/config", summary="Get Stripe Public Configuration")
def get_stripe_config():
    """
    Returns the public-facing Stripe configuration needed by the frontend,
    such as the public key and price IDs.
    """
    if not settings.STRIPE_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="Stripe public key is not configured.")
    
    return {
        "publicKey": settings.STRIPE_PUBLIC_KEY,
        "proPrice": settings.STRIPE_PRICE_PRO,
        "premiumPrice": settings.STRIPE_PRICE_PREMIUM,
    }

@router.get("/_debug-env", summary="Debug Stripe Environment")
def stripe_debug_env():
    """
    A debug endpoint to check the Stripe environment configuration.
    Should be disabled in a production environment.
    """
    if settings.ENV != "development":
        raise HTTPException(status_code=404, detail="Not found")

    key = settings.STRIPE_SECRET_KEY or ""
    return {
        "has_key": bool(key),
        "key_prefix": key[:6] if key else None,
        "webhook_secret_present": bool(settings.STRIPE_WEBHOOK_SECRET),
        "success_url": settings.STRIPE_SUCCESS_URL,
        "cancel_url": settings.STRIPE_CANCEL_URL,
    }