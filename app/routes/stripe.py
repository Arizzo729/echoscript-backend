import os, logging, stripe
log = logging.getLogger("startup")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # <-- MUST be set at runtime
if not stripe.api_key:
    log.error("STRIPE_SECRET_KEY is MISSING at runtime")

from fastapi import APIRouter
router = APIRouter(prefix="/api/stripe", tags=["stripe"])

@router.get("/_debug-env")
def stripe_debug_env():
    key = os.getenv("STRIPE_SECRET_KEY") or ""
    return {
        "has_key": bool(key),
        "len": len(key),
        "prefix": key[:6],
    }

@router.get("/_debug-prices")
def stripe_debug_prices():
    return {
        "pro": os.getenv("STRIPE_PRICE_PRO"),
        "premium": os.getenv("STRIPE_PRICE_PREMIUM"),
    }
