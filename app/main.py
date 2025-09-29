# app/main.py
import os
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "EchoScript API"
APP_VERSION = os.getenv("GIT_SHA", "local")

def _allowed_origins() -> list[str]:
    raw = os.getenv("API_ALLOWED_ORIGINS", "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def include_optional(module_path: str, attr: str = "router", prefix: str | None = None) -> None:
    """
    Import module_path and include FastAPI router named `attr`.
    If it fails, log but DO NOT crash the app.
    """
    try:
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        if prefix:
            app.include_router(router, prefix=prefix)
            print(f"[router] loaded: {module_path}.{attr} (prefix={prefix})")
        else:
            app.include_router(router)
            print(f"[router] loaded: {module_path}.{attr}")
    except Exception as e:
        print(f"[router] NOT loaded: {module_path}.{attr} -> {e}")

# --- Mount routers (guarded) ---
# Add or remove lines based on what you actually have in your repo.
include_optional("app.routes.auth")
include_optional("app.routes.contact")
include_optional("app.routes.export")
include_optional("app.routes.feedback")
include_optional("app.routes.history")
include_optional("app.routes.newsletter")
include_optional("app.routes.password_reset")
include_optional("app.routes.signup")
include_optional("app.routes.stripe_webhook")
include_optional("app.routes.transcribe")
include_optional("app.routes.transcripts")
include_optional("app.routes.verify_email")
include_optional("app.routes.video_task")
# Payments (if present)
include_optional("app.routers.paypal")
include_optional("app.routers.stripe_checkout")

# --- Health & meta routes ---
@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-api", "version": APP_VERSION}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    return {"ready": True}

@app.get("/version")
def version():
    return {"version": APP_VERSION}

