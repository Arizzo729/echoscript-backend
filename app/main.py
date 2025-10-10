# app/main.py  (full file)
import os
import logging
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

# --- logging ---
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
    """
    Mount routers that use relative prefixes (e.g., '/auth', '/contact').
    Do NOT put '/api' or '/v1' inside those router files.
    """
    modules = [
        "app.routes.health",
        "app.routes.contact",        # -> /api/contact and /v1/contact
        "app.routes.newsletter",
        "app.routes.auth",
        "app.routes.history",
        "app.routes.export",
        "app.routes.signup",
        "app.routes.password_reset",
        "app.routes.send_reset",
        "app.routes.paypal",
        "app.routes.paypal_health",
        # Add more relative-prefix routers here if needed:
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

# -------- Fallback contact endpoints (avoid 404 even if router import fails) --------
# Keep these after include_group so real routers win when present.
try:
    from pydantic import BaseModel, EmailStr
    class _ContactIn(BaseModel):
        name: str
        email: EmailStr
        subject: str
        message: str
        hp: str | None = None  # honeypot

    @app.post("/api/contact", name="contact_fallback_api")
    async def _contact_fallback_api(body: _ContactIn):
        # Accept and succeed even if email sender isn't configured yet
        if body.hp:  # bot trap
            return {"ok": True, "status": "discarded"}
        log.info("CONTACT_FALLBACK %s <%s> :: %s", body.name, body.email, body.subject)
        return {"ok": True, "status": "accepted"}

    @app.post("/v1/contact", name="contact_fallback_v1")
    async def _contact_fallback_v1(body: _ContactIn):
        if body.hp:
            return {"ok": True, "status": "discarded"}
        log.info("CONTACT_FALLBACK_V1 %s <%s> :: %s", body.name, body.email, body.subject)
        return {"ok": True, "status": "accepted"}
except Exception as e:
    log.warning("Fallback contact endpoints not added: %s", e)
