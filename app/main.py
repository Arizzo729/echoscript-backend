# app/main.py
import os
import logging
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("echoscript")

APP_VERSION = os.getenv("GIT_SHA", "local")

def parse_allowed_origins():
    raw = (os.getenv("API_ALLOWED_ORIGINS") or "").strip()
    if not raw:
        return ["*"]  # dev-friendly; tighten via env in prod
    return [o.strip() for o in raw.split(",") if o.strip()]

app = FastAPI(title="EchoScript API", version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
@app.get("/", response_class=PlainTextResponse)
def root_ok():
    return "ok"

@app.get("/api/healthz", response_class=PlainTextResponse)
def api_health():
    return "ok"

@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_health():
    return "ok"

def include_group(prefix: str):
    """Include routers under a prefix (we’ll call with /api and /v1)."""
    modules = [
        "app.routes.auth",
        "app.routes.contact",
        "app.routes.newsletter",
        "app.routes.stripe",
        "app.routes.transcribe",
        "app.routes.transcribe_stream",
        "app.routes.video_task",
    ]
    for mod in modules:
        try:
            m = importlib.import_module(mod)
            router = getattr(m, "router")
            app.include_router(router, prefix=prefix)
            log.info(f"Mounted {mod} at {prefix}")
        except Exception as e:
            log.warning(f"Skipping {mod}: {e}")

# Mount all routers under BOTH /api/* and /v1/*.
include_group("/api")
include_group("/v1")
