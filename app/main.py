# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.stripe_checkout import router as stripe_router
from app.routes.stripe_webhook import router as stripe_webhook_router
from app.routes.transcribe import router as transcribe_router

app = FastAPI(
    title="EchoScript API",
    version="1.0.0",
)

# --- CORS (allow your site + local dev) ---
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(health_router, prefix="")
app.include_router(auth_router,  prefix="/api/auth", tags=["Auth"])
app.include_router(stripe_router, prefix="/api/stripe", tags=["stripe"])
app.include_router(stripe_webhook_router, prefix="/api/stripe", tags=["Stripe Webhook"])
app.include_router(transcribe_router, prefix="/api/v1", tags=["transcription"])

# Root (optional)
@app.get("/", tags=["Root"])
def root():
    return {"ok": True, "version": "live", "env": "production"}

