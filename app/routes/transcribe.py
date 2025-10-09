# app/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "EchoScript API"
APP_VERSION = os.getenv("GIT_SHA", "local")
log = logging.getLogger("uvicorn")

def _csv(val: str | None) -> list[str]:
    return [x.strip() for x in (val or "").split(",") if x.strip()]

ALLOWED_ORIGINS = _csv(
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
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def _include_router_safe(import_path: str, name: str):
    try:
        module = __import__(import_path, fromlist=["router"])
        app.include_router(module.router)
        log.info("%s router loaded", name)
    except Exception as e:
        log.warning("%s router not loaded: %s", name, e)

# Core routes you already had
_include_router_safe("app.routes.auth", "Auth")
_include_router_safe("app.routes.stripe", "Stripe (legacy)")
_include_router_safe("app.routes.stripe_checkout", "Stripe checkout")
_include_router_safe("app.routes.stripe_webhook", "Stripe webhook")
_include_router_safe("app.routes.paypal", "PayPal")

# 🆕 Ensure media/transcription routers are mounted
_include_router_safe("app.routes.video_task", "Video tasks")

# 🆕 Back-compat endpoint expected by the frontend bundle:
#     POST https://api.echoscript.ai/v1/transcribe
_include_router_safe("app.routes.transcribe_v1", "Transcribe v1")

log.info("Allowed CORS origins: %s", cors_origins)

