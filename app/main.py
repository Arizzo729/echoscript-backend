# app/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = os.getenv("GIT_SHA", "live-min")

def allowed():
    raw = os.getenv("API_ALLOWED_ORIGINS", "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

# Toggle to control whether feature routers are mounted
ENABLE_FULL_ROUTERS = os.getenv("ENABLE_FULL_ROUTERS", "0").lower() in {"1", "true", "yes"}

app = FastAPI(title="EchoScript API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed(),
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

def _safe_include(module_path: str, attr: str = "router", prefix: str = "", tags: list[str] | None = None):
    """
    Import a module and include its FastAPI router if present.
    Any exception is logged, but startup continues (so the app still boots on Railway).
    """
    try:
        mod = __import__(module_path, fromlist=[attr])
        router = getattr(mod, attr)
        app.include_router(router, prefix=prefix, tags=tags or [])
        logging.getLogger(__name__).info("Mounted router: %s at %s", module_path, prefix or "/")
    except Exception as e:
        logging.getLogger(__name__).exception("Router %s failed to mount: %s", module_path, e)

# Only mount full routers when explicitly enabled
if ENABLE_FULL_ROUTERS:
    # auth (unchanged if you have it)
    _safe_include("app.routes.auth", prefix="/api/auth", tags=["auth"])
    # stripe — include BOTH real modules
    _safe_include("app.routes.stripe_checkout", prefix="/api/stripe", tags=["stripe"])
    _safe_include("app.routes.stripe_webhook", prefix="/api/stripe", tags=["stripe"])
    # transcribe
    _safe_include("app.routes.transcribe", prefix="/api/v1", tags=["transcribe"])

