import os
import logging
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

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


# -------- basic health --------
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
    Mount routers that use *relative* prefixes only (e.g., '/auth', '/contact').
    Do NOT put '/api' or '/v1' inside router files.
    """
    modules = [
        # 🔽 add only routers that declare relative prefixes
        "app.routes.health",
        "app.routes.contact",
        "app.routes.newsletter",
        "app.routes.auth",
        "app.routes.auth_alias",          # provides /auth/signin → login (redirect)
        "app.routes.feedback",
        "app.routes.history",
        "app.routes.export",
        "app.routes.signup",
        "app.routes.password_reset",
        "app.routes.send_reset",
        "app.routes.paypal",
        "app.routes.paypal_health",
        # If you have these with relative prefixes, uncomment them:
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


# Mount standard routers under /api and /v1
include_group("/api")
include_group("/v1")

# Mount compatibility endpoints ONCE with NO prefix.
# These expose absolute paths like /api/transcribe, /api/video-task, etc.
try:
    from app.routes import compact_endpoints as compat  # keep filename in sync
    app.include_router(compat.router)  # no prefix → avoids /api/api/*
    log.info("Mounted compat endpoints without prefix")
except Exception as e:
    log.warning("Compat endpoints not mounted: %s", e)
