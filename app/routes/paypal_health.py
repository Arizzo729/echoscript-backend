from fastapi import APIRouter
import os

router = APIRouter(prefix="/paypal", tags=["paypal"])

@router.get("/health")
def paypal_health():
    # Read env the same way the rest of your backend does
    env = (os.getenv("PAYPAL_ENV") or "sandbox").strip().lower()
    env = "live" if env.startswith("live") else "sandbox"

    has_client_id = bool((os.getenv("PAYPAL_CLIENT_ID") or "").strip())
    has_client_secret = bool((os.getenv("PAYPAL_CLIENT_SECRET") or "").strip())

    return {
        "ok": True,
        "env": env,
        "has_client_id": has_client_id,
        "has_client_secret": has_client_secret,
    }
