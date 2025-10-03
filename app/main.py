# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# ---- FastAPI app ----
app = FastAPI(title="EchoScript API", version="1.0.0")

# ---- CORS (frontend + local dev) ----
ALLOWED_ORIGINS = [
    "https://echoscript.ai",
    "https://www.echoscript.ai",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # cache preflight for a day
)

# ---- Always OK for preflight (avoids 405 on OPTIONS) ----
@app.options("/{path:path}")
async def preflight_ok(path: str):
    # CORSMiddleware adds the Access-Control-Allow-* headers
    return Response(status_code=200)

# ---- Simple root & health ----
@app.get("/")
async def root():
    return {"ok": True, "service": "echoscript-api", "version": app.version}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

# ---- Routers ----
# These modules should each define: router = APIRouter(prefix="...") with their own paths.
from app.routes.auth import router as auth_router
from app.routes.stripe_checkout import router as stripe_checkout_router
from app.routes.stripe_webhook import router as stripe_webhook_router
from app.routes.transcribe import router as transcribe_router
# If you also keep a health router file, you can include it too:
# from app.routes.health import router as health_router
# app.include_router(health_router)

app.include_router(auth_router)                 # e.g. /api/auth/*
app.include_router(stripe_checkout_router)      # e.g. /api/stripe/*
app.include_router(stripe_webhook_router)       # e.g. /api/stripe/webhook
app.include_router(transcribe_router)           # e.g. /api/v1/transcribe
