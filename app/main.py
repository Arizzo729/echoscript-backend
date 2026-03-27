from __future__ import annotations
import os, logging, importlib
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from pydantic import BaseModel

# EmailStr moved between pydantic versions; try common locations then fall back to plain str
try:
 from pydantic import EmailStr # type: ignore
except Exception:
 try:
  from pydantic.networks import EmailStr # type: ignore
 except Exception:
  # Fallback: accept plain strings where email validation isn't available
  EmailStr = str # type: ignore

from app.utils.send_email import send_email, EmailError

log = logging.getLogger("echoscript")
logging.basicConfig(level=logging.INFO)
APP_VERSION = os.getenv("GIT_SHA", "local")


def _allowed_origins() -> list[str]:
 raw = (os.getenv("API_ALLOWED_ORIGINS") or "").strip()

 if raw and raw != "*":
  return [o.strip() for o in raw.split(",") if o.strip()]

 return [
  "https://www.echoscript.ai",
  "https://echoscript.ai",
  "http://localhost:5173",
  "http://127.0.0.1:5173",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
 ]


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


@app.get("/api/healthz")
def api_health_ok() -> dict[str, str]:
 return {"status": "ok"}


@app.get("/v1/healthz", response_class=PlainTextResponse)
def v1_health_ok() -> str:
 return "ok"


CONTACT_ROUTER_MOUNTED = False


def include_group(prefix: str) -> None:
 global CONTACT_ROUTER_MOUNTED
 modules = [
  "app.routes.health", # optional
  "app.routes.contact",
  "app.routes.newsletter",
  "app.routes.auth",
  "app.routes.history",
  "app.routes.export",
  "app.routes.signup",
  "app.routes.password_reset",
  "app.routes.send_reset",
  # NOTE: paypal router is mounted explicitly below because it already has /api prefix
  "app.routes.paypal_health",
  "app.routes.assistant",
  "app.routes.transcripts",
  "app.routes.usage",
  "app.routes.transcribe",
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


include_group("/api/v1")
include_group("/v1")

# Legacy mounts for frontend paths like /api/auth/me and /api/transcribe/...
try:
 from app.routes.auth import router as auth_router
 app.include_router(auth_router, prefix="/api")
 log.info("Mounted auth router at /api/auth")
except Exception as e:
 log.warning("Auth /api mount failed: %s", e)

try:
 from app.routes.transcribe import router as transcribe_router
 app.include_router(transcribe_router, prefix="/api")
 log.info("Mounted transcribe router at /api/transcribe")
except Exception as e:
 log.warning("Transcribe /api mount failed: %s", e)

# Ensure /api/paypal/* exists exactly as frontend expects.
try:
 from app.routes.paypal import router as paypal_router
 app.include_router(paypal_router)
 log.info("Mounted paypal router at absolute /api/paypal")
except Exception as e:
 log.warning("PayPal absolute /api mount failed: %s", e)

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

# Stripe payment routes
try:
 from app.routes.stripe import router as stripe_router
 app.include_router(stripe_router, prefix="/api")
 log.info("Mounted Stripe router at /api/stripe")
except Exception as e:
 log.warning("Stripe endpoints not mounted: %s", e)

try:
 from app.routes.stripe_checkout import router as stripe_checkout_router
 app.include_router(stripe_checkout_router)
 log.info("Mounted Stripe checkout router at /api/stripe/checkout")
except Exception as e:
 log.warning("Stripe checkout endpoints not mounted: %s", e)

try:
 from app.routes.stripe_webhook import router as stripe_webhook_router
 app.include_router(stripe_webhook_router)
 log.info("Mounted Stripe webhook router at /api/stripe/webhook")
except Exception as e:
 log.warning("Stripe webhook endpoints not mounted: %s", e)

# Fallback contact if the main contact router didn't import
if not CONTACT_ROUTER_MOUNTED:
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
   f"Email: {payload.get('email')}\n"
   f"Subject: {payload.get('subject')}\n\n"
   f"Message:\n{payload.get('message')}\n"
  )
  html = (
   f" New contact submission "
   f" Name: {payload.get('name')} "
   f" Email: {payload.get('email')} "
   f" Subject: {payload.get('subject')} "
   f" {payload.get('message')} "
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
 have_smtp = all(bool(os.getenv(k)) for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_FROM"])
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
   body_html=" If you see this, HTTP email is working ✅ ",
   reply_to="no-reply@echoscript.ai",
  )
  return {"ok": True}
 except EmailError as e:
  raise HTTPException(status_code=500, detail=str(e))
