# app/main.py

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# --------------------------------------------------------------------------------------
# App metadata / version
# --------------------------------------------------------------------------------------
APP_NAME = "EchoScript API"
APP_VERSION = os.getenv("GIT_SHA", "local")

log = logging.getLogger("uvicorn")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# --------------------------------------------------------------------------------------
# CORS
# Prefer env var:
#   API_ALLOWED_ORIGINS="https://echoscript.ai,https://www.echoscript.ai,http://localhost:5173"
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# Ensure DB schema on startup (idempotent) — IMPORT MODELS BEFORE create_all()
# --------------------------------------------------------------------------------------
try:
    from app.db import Base, engine
    import app.models  # <-- ensures SQLAlchemy metadata knows your models
except Exception:
    try:
        from app.database import Base, engine  # type: ignore
        import app.models  # type: ignore
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

# --------------------------------------------------------------------------------------
# Health / root
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# Routers (defensive import so one failure doesn't kill the app)
# Each router defines its own prefix, e.g. "/api/auth", "/api/v1", etc.
# --------------------------------------------------------------------------------------
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

log.info("Allowed CORS origins: %s", ALLOWED_ORIGINS)
