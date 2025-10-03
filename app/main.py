# app/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = os.getenv("GIT_SHA", "live-min")

def _allowed_origins() -> list[str]:
    raw = (os.getenv("API_ALLOWED_ORIGINS", "") or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

ENABLE_FULL_ROUTERS = os.getenv("ENABLE_FULL_ROUTERS", "0").lower() in {"1", "true", "yes"}

app = FastAPI(title="EchoScript API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-api", "version": APP_VERSION}

@app.get("/healthz")
def healthz():
    return {"ok": True, "version": APP_VERSION}

@app.get("/version")
def version():
    return {"version": APP_VERSION}

def _safe_include(module_path: str, attr: str = "router", prefix: str | None = None, tags: list[str] | None = None):
    """Import module and include its FastAPI router."""
    try:
        mod = __import__(module_path, fromlist=[attr])
        router = getattr(mod, attr)
        if prefix:
            app.include_router(router, prefix=prefix, tags=tags or [])
        else:
            app.include_router(router, tags=tags or [])
        logging.getLogger(__name__).info("Mounted router: %s", module_path)
    except Exception as e:
        logging.getLogger(__name__).exception("Router %s failed to mount: %s", module_path, e)

if ENABLE_FULL_ROUTERS:
    # Auth
    _safe_include("app.routes.auth")         # /api/auth login/refresh  :contentReference[oaicite:7]{index=7}
    _safe_include("app.routes.signup")       # /api/auth/signup        (NEW)

    # Stripe (already have their own /api/stripe prefix)
    _safe_include("app.routes.stripe_checkout")  # create-checkout-session  :contentReference[oaicite:8]{index=8}
    _safe_include("app.routes.stripe_webhook")   # webhook handler           :contentReference[oaicite:9]{index=9}

    # Transcription (leave as-is)
    _safe_include("app.routes.transcribe")
