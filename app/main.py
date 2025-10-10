# app/main.py
from __future__ import annotations

import os
import logging
import importlib
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from pydantic import BaseModel, EmailStr

# HTTP-first email sender with SMTP fallback
from app.utils.send_email import send_email, EmailError

# -----------------------------------------------------------------------------
# Logging / version
# -----------------------------------------------------------------------------
log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)
APP_VERSION = os.getenv("GIT_SHA", "local")

# -----------------------------------------------------------------------------
# App + CORS
# -----------------------------------------------------------------------------
def _allowed_origins() -> list[str]:
    raw = (os.getenv("API_ALLOWED_ORIGINS") or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

app = FastAPI(title="EchoScript API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic liveness
@app.get("/", response_class=PlainTextResponse)
def root_ok() -> str:
    return "ok"

# Simple health (your richer DB/Redis/Stripe checks live in app.routes.health)
@app.get("/api/healthz", response_class=PlainTextResponse)
def api_health_ok() -> str:
    return "ok"

@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_health_ok() -> str:
    return "ok"

# -----------------------------------------------------------------------------
# Router mounting
# -----------------------------------------------------------------------------
CONTACT_ROUTER_MOUNTED = False  # set True if app.routes.contact is included successfully

def include_group(prefix: str) -> None:
    """Mount routers that expect a relative prefix. We mount at both /api and /v1."""
    global CONTACT_ROUTER_MOUNTED
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
        # Optional: enable when you’re ready
        # "app.routes.transcribe",
        # "app.routes.transcribe_stream",
        # "app.routes.video_task",
        # "app.routes.subtitles",
        # "app.routes.transcripts",
        # "app.routes.translate",
        # "app.routes.stripe",
    ]
    for mod in modules:
        try:
            m = importlib.import_module(mod)
            router = getattr(m, "router")
            app.include_router(router, prefix=prefix)
            log.info("Mounted %s at %s", mod, prefix)
            if mod.endswith(".contact"):
                CONTACT_ROUTER_MOUNTED = True
        except Exception as e:
            log.warning("Skipping %s: %s", mod, e)

# Mount under both namespaces
include_group("/api")
include_group("/v1")

# Routers that already declare absolute paths (so no extra prefix)
try:
    from app.routes import compact_endpoints as compat
    app.include_router(compat.router)
    log.info("Mounted compat endpoints without prefix")
except Exception as e:
    log.warning("Compat endpoints not mounted: %s", e)

try:
    from app.routes.feedback import router as feedback_router
    app.include_router(feedback_router)
    log.info("Mounted feedback router at its absolute path")
except Exception as e:
    log.warning("Feedback endpoints not mounted: %s", e)

# -----------------------------------------------------------------------------
# Email utilities for contact flow
# -----------------------------------------------------------------------------
def _contact_to_default() -> str:
    return (
        os.getenv("RESEND_TO")
        or os.getenv("SMTP_TO")
        or os.getenv("CONTACT_TO")
        or "support@echoscript.ai"
    )

def _send_contact_email(payload: dict) -> None:
    """Send via HTTP provider (Resend) if configured; otherwise try SMTP."""
    to_addr = payload.get("to") or _contact_to_default()
    subj = f"[EchoScript Contact] {payload.get('subject','(no subject)')}"
    body_text = (
        "New contact submission:\n\n"
        f"Name: {payload.get('name')}\n"
        f"Email: {payload.get('email')}\n"
        f"Subject: {payload.get('subject')}\n\n"
        f"Message:\n{payload.get('message')}\n"
    )
    body_html = f"""
    <h2>New contact submission</h2>
    <p><b>Name:</b> {payload.get('name')}</p>
    <p><b>Email:</b> {payload.get('email')}</p>
    <p><b>Subject:</b> {payload.get('subject')}</p>
    <hr/>
    <pre style="white-space:pre-wrap">{payload.get('message')}</pre>
    """
    send_email(
        to_address=to_addr,
        subject=subj,
        body_text=body_text,
        body_html=body_html,
        reply_to=payload.get("email"),
    )
    log.info("CONTACT_EMAIL_SENT to=%s", to_addr)

# -----------------------------------------------------------------------------
# Fallback contact endpoints
#   Only register these if app.routes.contact failed to import,
#   so we don't collide with your proper contact router.
# -----------------------------------------------------------------------------
if not CONTACT_ROUTER_MOUNTED:
    class _ContactIn(BaseModel):
        name: str
        email: EmailStr
        subject: str
        message: str
        hp: Optional[str] = None  # honeypot
        to: Optional[EmailStr] = None  # optional override

    @app.post("/api/contact", name="contact_fallback_api")
    async def _contact_fallback_api(body: _ContactIn, bg: BackgroundTasks):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        payload = body.model_dump()
        log.info("CONTACT_FALLBACK %s <%s> :: %s", body.name, body.email, body.subject)
        bg.add_task(_send_contact_email, payload)
        return {"ok": True, "status": "accepted"}

    @app.post("/v1/contact", name="contact_fallback_v1")
    async def _contact_fallback_v1(body: _ContactIn, bg: BackgroundTasks):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        payload = body.model_dump()
        log.info("CONTACT_FALLBACK_V1 %s <%s> :: %s", body.name, body.email, body.subject)
        bg.add_task(_send_contact_email, payload)
        return {"ok": True, "status": "accepted"}

# -----------------------------------------------------------------------------
# Simple email test endpoint (always available)
# -----------------------------------------------------------------------------
@app.post("/api/contact/test")
def contact_test():
    try:
        _send_contact_email({
            "name": "System",
            "email": "no-reply@echoscript.ai",
            "subject": "EchoScript email test",
            "message": "If you see this, HTTP email is working ✅",
        })
        return {"ok": True}
    except EmailError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected: {e}")

# -----------------------------------------------------------------------------
# Diagnostics (no secrets)
#   Call: GET /api/_diag/email
# -----------------------------------------------------------------------------
diag_router = APIRouter(prefix="/_diag", tags=["diag"])

@diag_router.get("/email")
def diag_email():
    have_resend = bool(os.getenv("RESEND_API_KEY"))
    have_smtp = all(bool(os.getenv(k)) for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_FROM"])
    mode = "HTTP" if have_resend else ("SMTP" if have_smtp else "NONE")
    return {
        "mode": mode,
        "resend_api_key_present": have_resend,
        "smtp_config_present": have_smtp,
        "to": _contact_to_default(),
        "from": os.getenv("EMAIL_FROM")
                or os.getenv("RESEND_FROM")
                or os.getenv("SMTP_FROM")
                or "noreply@onresend.com",
    }

app.include_router(diag_router, prefix="/api")

# deploy-bump

