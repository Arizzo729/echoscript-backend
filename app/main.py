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

def _include_router_safe(import_path: str, name: str):
    try:
        module = __import__(import_path, fromlist=["router"])
        app.include_router(module.router)
        log.info("%s router loaded", name)
    except Exception as e:
        log.warning("%s router not loaded: %s", name, e)

# Include routes
_include_router_safe("app.routes.auth", "Auth")                 # <-- added
_include_router_safe("app.routes.stripe", "Stripe (legacy)")
_include_router_safe("app.routes.stripe_checkout", "Stripe checkout")
_include_router_safe("app.routes.stripe_webhook", "Stripe webhook")
_include_router_safe("app.routes.paypal", "PayPal")

log.info("Allowed CORS origins: %s", cors_origins)
