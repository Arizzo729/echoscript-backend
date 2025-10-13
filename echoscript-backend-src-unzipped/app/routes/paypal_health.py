# app/routes/paypal_health.py
from fastapi import APIRouter
from app.core.settings import settings

router = APIRouter(prefix="/paypal-health", tags=["Health", "PayPal"])

@router.get("/")
def paypal_health_check():
    """
    Provides a health check for the PayPal integration.
    
    Returns the configured environment and whether the client ID and secret are present.
    """
    return {
        "ok": True,
        "environment": settings.PAYPAL_ENV,
        "client_id_present": bool(settings.PAYPAL_CLIENT_ID),
        "client_secret_present": bool(settings.PAYPAL_CLIENT_SECRET),
    }