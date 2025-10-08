import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "EchoScript API"
APP_VERSION = os.getenv("GIT_SHA", "local")
log = logging.getLogger("uvicorn")

def _split_csv(val: str | None) -> list[str]:
    return [x.strip() for x in (val or "").split(",") if x.strip()]

ALLOWED_ORIGINS = _split_csv(
    os.getenv("ALLOW_ORIGINS")
    or os.getenv("CORS_ORIGINS")
    or os.getenv("API_ALLOWED_ORIGINS")
    or "*"
)
cors_origins = ["*"] if ALLOWED_ORIGINS == ["*"] else ALLOWED_ORIGINS

app = FastAPI(title=APP_NAME, version=APP_VERSION)

@app.get("/api/healthz")
def healthz():
    return {"ok": True}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# ---- Mount routers (AUTH IS CRITICAL) ----
from app.routes.auth import router as auth_router
app.include_router(auth_router)  # auth.py has prefix="/api/auth"

# Optional/keep if present
try:
    from app.routes.stripe import router as stripe_legacy
    app.include_router(stripe_legacy)
except Exception as e:
    log.warning("Stripe (legacy) router not loaded: %s", e)

try:
    from app.routes.stripe_checkout import router as stripe_checkout
    app.include_router(stripe_checkout)
except Exception as e:
    log.warning("Stripe checkout router not loaded: %s", e)

try:
    from app.routes.stripe_webhook import router as stripe_webhook
    app.include_router(stripe_webhook)
except Exception as e:
    log.warning("Stripe webhook router not loaded: %s", e)

try:
    from app.routes.paypal import router as paypal_router
    app.include_router(paypal_router)
except Exception as e:
    log.warning("PayPal router not loaded: %s", e)

log.info("Allowed CORS origins: %s", cors_origins)

