from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routes.auth import router as auth_router
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

@app.get("/")
def root():
    return {"ok": True, "service": "echoscript-backend", "env": ENV}

@app.get("/healthz")
def healthz():
    return {"ok": True, "version": "live", "env": ENV}

# 👇 the important part
app.include_router(auth_router,   prefix="/api/auth",   tags=["auth"])
app.include_router(stripe_router, prefix="/api/stripe", tags=["stripe"])
