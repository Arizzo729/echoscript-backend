"""
Minimal development ASGI entrypoint for EchoScript backend.
This file mounts route modules from `app.routes` and provides
startup logic for local development. It intentionally keeps
behavior small and predictable to make debugging easier.
"""

import os
import logging
import importlib
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel


load_dotenv()

# EmailStr fallback for different pydantic versions
try:
    from pydantic import EmailStr  # type: ignore
except Exception:
    try:
        from pydantic.networks import EmailStr  # type: ignore
    except Exception:
        EmailStr = str  # type: ignore


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
APP_VERSION = os.getenv("GIT_SHA", "dev")

log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EchoScript API (dev)", version=APP_VERSION)


def _allowed_origins() -> list[str]:
    raw = (os.getenv("API_ALLOWED_ORIGINS") or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mount_all_routes():
    """Import and include routers from app.routes modules."""
    modules = [
        "app.routes.health",
        "app.routes.contact",
        "app.routes.newsletter",
        "app.routes.auth",
        "app.routes.history",
        "app.routes.export",
        "app.routes.signup",
        "app.routes.password_reset",
        "app.routes.send_reset",
        "app.routes.paypal",
        "app.routes.paypal_health",
        "app.routes.assistant",
        "app.routes.transcripts",
        "app.routes.usage",
        "app.routes.profile",
    ]

    for prefix in ["/api/v1", "/v1"]:
        for mod in modules:
            try:
                m = importlib.import_module(mod)
                router = getattr(m, "router")
                app.include_router(router, prefix=prefix)
                log.info("Mounted %s at %s", mod, prefix)
            except Exception as e:
                log.warning("Skipping %s: %s", mod, e)

    # Compat endpoints that already have absolute paths
    try:
        compat = importlib.import_module("app.routes.compact_endpoints")
        app.include_router(compat.router)
        log.info("Mounted compat endpoints without prefix")
    except Exception as e:
        log.warning("Compat endpoints not mounted: %s", e)


def _add_fallback_contact():
    """Mount a small fallback contact endpoint if the real router fails to load."""
    try:
        from app.utils.send_email import send_email
    except Exception:
        log.warning("send_email not available; skipping fallback contact")
        return

    class _ContactIn(BaseModel):
        name: str
        email: EmailStr
        subject: str
        message: str
        hp: Optional[str] = None
        to: Optional[EmailStr] = None

    def _contact_to_default() -> str:
        return os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai"

    def _send_contact_email(payload: dict) -> None:
        subj = f"[EchoScript Contact] {payload.get('subject','(no subject)')}"
        text = (
            "New contact submission:\n\n"
            f"Name: {payload.get('name')}\n"
            f"Email: {payload.get('email')}\n\n"
            f"Message:\n{payload.get('message')}\n"
        )
        html = (
            f"<h2>New contact submission</h2>"
            f"<p><b>Name:</b> {payload.get('name')}</p>"
            f"<p><b>Email:</b> {payload.get('email')}</p>"
            f"<hr/><pre style='white-space:pre-wrap'>{payload.get('message')}</pre>"
        )
        to_addr = payload.get("to") or _contact_to_default()
        send_email(to_addr, subj, text, html, reply_to=payload.get("email"))

    @app.post("/api/contact")
    async def _contact_fallback_api(body: _ContactIn, bg: BackgroundTasks):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        bg.add_task(_send_contact_email, body.model_dump())
        return {"ok": True, "status": "accepted"}


@app.on_event("startup")
def on_startup():
    Path("data").mkdir(parents=True, exist_ok=True)
    _mount_all_routes()
    # Add fallback contact if contact router didn't mount
    _add_fallback_contact()


@app.get("/")
def root_ok() -> dict:
    return {"status": "ok", "version": app.version}


@app.get("/api/healthz")
def api_health_ok() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_health_ok() -> str:
    return "ok"
