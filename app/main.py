# app/main.py
import os, logging, importlib
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from pydantic import BaseModel, EmailStr

from app.utils.send_email import send_email, EmailError

log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)

APP_VERSION = os.getenv("GIT_SHA", "local")

def _allowed_origins():
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

# -------- health --------
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
    """Mount routers that use relative prefixes (no /api in the file)."""
    modules = [
        "app.routes.health",
        "app.routes.contact",        # -> /api/contact and /v1/contact (if file exists)
        "app.routes.newsletter",
        "app.routes.auth",
        "app.routes.history",
        "app.routes.export",
        "app.routes.signup",
        "app.routes.password_reset",
        "app.routes.send_reset",
        "app.routes.paypal",
        "app.routes.paypal_health",
        # Add more here if you want them under /api and /v1
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
        except Exception as e:
            log.warning("Skipping %s: %s", mod, e)

# Mount standard routers under /api and /v1 (only those that import cleanly)
include_group("/api")
include_group("/v1")

# Mount compatibility endpoints (already declare absolute '/api/*' paths)
try:
    from app.routes import compact_endpoints as compat
    app.include_router(compat.router)  # no prefix to avoid '/api/api/*'
    log.info("Mounted compat endpoints without prefix")
except Exception as e:
    log.warning("Compat endpoints not mounted: %s", e)

# Mount feedback (this router already uses prefix='/api/feedback')
try:
    from app.routes.feedback import router as feedback_router
    app.include_router(feedback_router)  # no extra prefix
    log.info("Mounted feedback router at its absolute path")
except Exception as e:
    log.warning("Feedback endpoints not mounted: %s", e)

# -------- Email helpers (HTTP-first) --------
def _send_contact_email(payload: dict) -> None:
    """
    Send contact email via HTTP provider (Resend) if configured; otherwise try SMTP.
    Env:
      - RESEND_API_KEY  (HTTP path)
      - EMAIL_FROM or RESEND_FROM (display "From")
      - RESEND_TO or SMTP_TO or CONTACT_TO (recipient) — defaults to support@echoscript.ai
      - SMTP_*          (fallback)
    """
    to_addr = (
        os.getenv("RESEND_TO")
        or os.getenv("SMTP_TO")
        or os.getenv("CONTACT_TO")
        or "support@echoscript.ai"
    )
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

    try:
        send_email(
            to_address=to_addr,
            subject=subj,
            body_text=body_text,
            body_html=body_html,
            reply_to=payload.get("email"),
        )
        log.info("CONTACT_EMAIL_SENT to %s", to_addr)
    except EmailError as e:
        log.error("CONTACT_EMAIL_FAILED: %s", e)
        raise

# -------- Fallback contact endpoints (work even if contact router fails to import) --------
class _ContactIn(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    hp: str | None = None  # honeypot

@app.post("/api/contact", name="contact_fallback_api")
async def _contact_fallback_api(body: _ContactIn, bg: BackgroundTasks):
    if body.hp:  # bot trap
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

# Quick verification endpoint
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# deploy-bump (HTTP email)

