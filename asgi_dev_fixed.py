"""
Very small, robust ASGI entrypoint for development.
This minimal version provides a health endpoint and attempts
to include `app.routes.health` if present. Use this to
guarantee the backend can start while you iterate.
"""

import importlib
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


load_dotenv()

log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EchoScript API (dev)")


@app.on_event("startup")
def _startup():
    Path("data").mkdir(parents=True, exist_ok=True)
    # Try to mount the basic health/router if available
    try:
        m = importlib.import_module("app.routes.health")
        app.include_router(m.router, prefix="/api/v1")
        log.info("Mounted app.routes.health at /api/v1")
    except Exception as e:
        log.warning("Could not mount app.routes.health: %s", e)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/api/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_healthz():
    return "ok"
