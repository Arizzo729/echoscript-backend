# app/main.py — EchoScript API (FINAL)

import os
import logging
from importlib import import_module
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

APP_NAME = "EchoScript API"
APP_VERSION = os.getenv("GIT_SHA", "local")

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("uvicorn")

def _mask(v: str | None) -> str | None:
    if not v:
        return None
    return f"{v[:6]}…{v[-4:]}" if len(v) > 10 else v[:3] + "…"

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(title=APP_NAME, version=APP_VERSION)

# -----------------------------------------------------------------------------
# CORS
#   Prefer env var:
#   API_ALLOWED_ORIGINS="https://echoscript.ai,https://www.echoscript.ai,http://localhost:5173"
# -----------------------------------------------------------------------------
raw_allowed = (os.getenv("API_ALLOWED_ORIGINS") or "").strip()
if not raw_allowed or raw_allowed == "*":
    ALLOWED_ORIGINS = [
        "https://echoscript.ai",
        "https://www.echoscript.ai",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
else:
    ALLOWED_ORIGINS = [o.strip() for o in raw_allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# -----------------------------------------------------------------------------
# DB bootstrap (idempotent). Avoid shadowing the FastAPI "app" name.
# -----------------------------------------------------------------------------
try:
    from app.db import Base, engine  # your SQLAlchemy Base/engine
    import_module("app.models")      # register models
except Exception:
    try:
        from app.database import Base, engine  # type: ignore
        import_module("app.models")            # type: ignore
    except Exception:
        Base = engine = None  # type: ignore

if Base is not None and engine is not None:
    @app.on_event("startup")
    def _ensure_db() -> None:
        try:
            Base.metadata.create_all(bind=engine)
            log.info("DB: ensured tables exist")
        except Exception as e:
            log.warning("DB init error: %s", e)

# -----------------------------------------------------------------------------
# Startup env log (sanitized)
# -----------------------------------------------------------------------------
@app.on_event("startup")
def _log_env():
    log.info(
        "ENV LOADED: app_version=%s allowed_origins=%s stripe_key=%s price_pro=%s price_premium=%s",
        APP_VERSION,
        ALLOWED_ORIGINS,
        _mask(os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")),
        os.getenv("STRIPE_PRICE_PRO"),
        os.getenv("STRIPE_PRICE_PREMIUM"),
    )

# -----------------------------------------------------------------------------
# Health / root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-api", "version": APP_VERSION}

@app.get("/healthz")
def healthz_root():
    return {"ok": True}

@app.get("/api/healthz")
def healthz_api():
    return {"ok": True}

@app.head("/api/healthz")
def healthz_api_head():
    return Response(status_code=200)

# OPTIONS catch-all so browsers never get 405 on preflight
@app.options("/{path:path}")
async def preflight_ok(path: str):
    return Response(status_code=200)

# -----------------------------------------------------------------------------
# Debug helpers (safe): verify Stripe env at runtime without touching Stripe router
# -----------------------------------------------------------------------------
@app.get("/api/_debug/stripe/env")
def _debug_stripe_env():
    key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET") or ""
    return {"has_key": bool(key), "len": len(key), "prefix": key[:6] if key else ""}

@app.get("/api/_debug/stripe/prices")
def _debug_stripe_prices():
    return {"pro": os.getenv("STRIPE_PRICE_PRO"), "premium": os.getenv("STRIPE_PRICE_PREMIUM")}

# -----------------------------------------------------------------------------
# Routers (defensive include so one failure doesn’t kill the app)
# -----------------------------------------------------------------------------
def _include_router_safe(import_path: str, name: str):
    try:
        module = __import__(import_path, fromlist=["router"])
        app.include_router(module.router)
        log.info("%s router loaded", name)
    except Exception as e:
        log.warning("%s router not loaded: %s", name, e)

_include_router_safe("app.routes.auth", "Auth")
_include_router_safe("app.routes.stripe_checkout", "Stripe checkout")
_include_router_safe("app.routes.stripe_webhook", "Stripe webhook")
_include_router_safe("app.routes.transcribe", "Transcribe")
_include_router_safe("app.routes.paypal", "PayPal")

log.info("Allowed CORS origins: %s", ALLOWED_ORIGINS)
