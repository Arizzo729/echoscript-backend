# app/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Payments
from app.routers import paypal as paypal_router
from app.routers.stripe_checkout import router as stripe_checkout_router

# Routers (keep the ones you actually have in your repo)
from app.routes.auth import router as auth_router
from app.routes.contact import router as contact_router
from app.routes.export import router as export_router
from app.routes.feedback import router as feedback_router
from app.routes.history import router as history_router
from app.routes.newsletter import router as newsletter_router
from app.routes.password_reset import router as password_reset_router
from app.routes.signup import router as signup_router
from app.routes.stripe_webhook import router as stripe_webhook_router
from app.routes.transcribe import router as transcribe_router
from app.routes.transcripts import router as transcripts_router
from app.routes.verify_email import router as verify_email_router
from app.routes.video_task import router as video_task_router


def _allowed_origins() -> list[str]:
    raw = os.getenv("API_ALLOWED_ORIGINS", "*").strip()
    if raw == "*" or raw == "":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="EchoScript API", version=os.getenv("GIT_SHA", "local"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth_router)
app.include_router(contact_router)
app.include_router(export_router)
app.include_router(feedback_router)
app.include_router(history_router)
app.include_router(newsletter_router)
app.include_router(password_reset_router)
app.include_router(signup_router)
app.include_router(stripe_webhook_router)
app.include_router(transcribe_router)
app.include_router(transcripts_router)
app.include_router(verify_email_router)
app.include_router(video_task_router)

# payments
app.include_router(paypal_router.router)
app.include_router(stripe_checkout_router)


@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-api"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"ready": True}


@app.get("/version")
def version():
    return {"version": os.getenv("GIT_SHA", "local")}
