# app/main.py
from __future__ import annotations

import logging
import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from app.core.settings import settings

# -----------------------------------------------------------------------------
# Logging & App Initialization
# -----------------------------------------------------------------------------

log = logging.getLogger("echoscript")
logging.basicConfig(level=settings.LOG_LEVEL.upper())

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Core API Endpoints
# -----------------------------------------------------------------------------

@app.get("/", response_class=PlainTextResponse, include_in_schema=False)
def root_ok() -> str:
    return "ok"

@app.get("/api/healthz", response_class=PlainTextResponse, tags=["Health"])
def api_health_ok() -> str:
    return "ok"

# -----------------------------------------------------------------------------
# Dynamic Router Mounting
# -----------------------------------------------------------------------------

def include_router_from_module(module_name: str, prefix: str):
    """Helper to import and include a router from a given module."""
    try:
        module = importlib.import_module(module_name)
        app.include_router(module.router, prefix=prefix)
        log.info(f"Mounted {module_name} at {prefix}")
    except (ImportError, AttributeError) as e:
        log.warning(f"Skipping router {module_name}: {e}")

# Mount routers with a common prefix
API_V1_PREFIX = "/api"

# List of routers to be mounted under the /api prefix
ROUTERS_TO_MOUNT = [
    "app.routes.auth",
    "app.routes.contact",
    "app.routes.email_test",
    "app.routes.export",
    "app.routes.feedback",
    "app.routes.health",
    "app.routes.history",
    "app.routes.newsletter",
    "app.routes.password_reset",
    "app.routes.paypal",
    "app.routes.paypal_health",
    "app.routes.send_reset",
    "app.routes.signup",
    "app.routes.stripe",
    "app.routes.stripe_checkout",
    "app.routes.stripe_webhook",
    "app.routes.subtitles",
    "app.routes.summary",
    "app.routes.transcribe",
    "app.routes.transcribe_stream",
    "app.routes.transcripts",
    "app.routes.translate",
    "app.routes.verify_email",
    "app.routes.video_task",
]

for router_module in ROUTERS_TO_MOUNT:
    include_router_from_module(router_module, prefix=API_V1_PREFIX)

# Mount routers that have their own absolute paths
try:
    from app.routes import compact_endpoints as compat
    app.include_router(compat.router)
    log.info("Mounted compact_endpoints without prefix")
except Exception as e:
    log.warning(f"Compat endpoints not mounted: {e}")

log.info("Application startup complete.")