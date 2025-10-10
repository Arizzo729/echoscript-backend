from __future__ import annotations
import os, logging, importlib
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from pydantic import BaseModel, EmailStr
from app.utils.send_email import send_email, EmailError

log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)
APP_VERSION = os.getenv("GIT_SHA", "local")

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

@app.get("/", response_class=PlainTextResponse)
def root_ok() -> str:
    return "ok"

@app.get("/api/healthz", response_class=PlainTextResponse)
def api_health_ok() -> str:
    return "ok"

@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_health_ok() -> str:
    return "ok"

CONTACT_ROUTER_MOUNTED = False

def include_group(prefix: str) -> None:
    global CONTACT_ROUTER_MOUNTED
    modules = [
        "app.routes.health",          # optional
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
    ]
    for mod in modules:
        try:
            m = importlib.import_module(mod)
            router = getattr(m, "router")
            app.include_router(router, prefix=prefix)
            if mod.endswith(".contact"):
                CONTACT_ROUTER_MOUNTED = True
            log.info("Mounted %s at %s", mod, prefix)
        except Exception as e:
            log.warning("Skipping %s: %s", mod, e)

include_group("/api")
include_group("/v1")

# Compat routes that already have absolute paths
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

# Fallback contact if the main contact router didn't import
if not CONTACT_ROUTER_MOUNTED:
    class _ContactIn(BaseModel):
        name: str
        email: EmailStr
        subject: str
        message: str
        hp: Optional[str] = None
        to: Optional[EmailStr] = None

    from fastapi import BackgroundTasks
    def _contact_to_default() -> str:
        return os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai"

    def _send_contact_email(payload: dict) -> None:
        subj = f"[EchoScript Contact] {payload.get('subject','(no subject)')}"
        text = (
            "New contact submission:\n\n"
            f"Name: {payload.get('name')}\n"
            f"Email: {payload.get('email')}\n"
            f"Subject: {payload.get('subject')}\n\n"
            f"Message:\n{payload.get('message')}\n"
        )
        html = (
            f"<h2>New contact submission</h2>"
            f"<p><b>Name:</b> {payload.get('name')}</p>"
            f"<p><b>Email:</b> {payload.get('email')}</p>"
            f"<p><b>Subject:</b> {payload.get('subject')}</p>"
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

    @app.post("/v1/contact")
    async def _contact_fallback_v1(body: _ContactIn, bg: BackgroundTasks):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        bg.add_task(_send_contact_email, body.model_dump())
        return {"ok": True, "status": "accepted"}

# Diagnostics
diag = APIRouter(prefix="/_diag", tags=["diag"])

@diag.get("/email")
def diag_email():
    have_resend = bool(os.getenv("RESEND_API_KEY"))
    have_smtp = all(bool(os.getenv(k)) for k in ["SMTP_HOST","SMTP_PORT","SMTP_USER","SMTP_PASS","SMTP_FROM"])
    mode = "HTTP" if have_resend else ("SMTP" if have_smtp else "NONE")
    return {
        "mode": mode,
        "resend_api_key_present": have_resend,
        "smtp_config_present": have_smtp,
        "to": os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai",
        "from": os.getenv("EMAIL_FROM") or os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM") or "noreply@onresend.com",
    }

app.include_router(diag, prefix="/api")

# Built-in email test
@app.post("/api/contact/test")
def contact_test():
    try:
        send_email(
            to_address=os.getenv("RESEND_TO") or os.getenv("SMTP_TO") or os.getenv("CONTACT_TO") or "support@echoscript.ai",
            subject="EchoScript email test",
            body_text="If you see this, HTTP email is working ✅",
            body_html="<p>If you see this, <b>HTTP email</b> is working ✅</p>",
            reply_to="no-reply@echoscript.ai",
        )
        return {"ok": True}
    except EmailError as e:
        raise HTTPException(status_code=500, detail=str(e))
