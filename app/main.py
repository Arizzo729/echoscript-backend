# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routes.stripe_checkout import router as stripe_router

ENV = os.getenv("ENV", "production")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "https://echoscript.ai,https://www.echoscript.ai").split(",")

app = FastAPI(title="EchoScript API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOW_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True, "version": "live", "env": ENV}

# Mirror under /api just in case the frontend calls this path
@app.get("/api/healthz")
def api_healthz():
    return {"ok": True, "version": "live", "env": ENV}

# --- Mount feature routers under /api/... ---
app.include_router(stripe_router, prefix="/api/stripe", tags=["stripe"])

# Optional: root welcome
@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-backend"}
