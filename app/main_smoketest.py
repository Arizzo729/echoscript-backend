from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.config import settings
except Exception:
    class _S: APP_NAME="EchoScript API"; API_PREFIX="/api"; CORS_ALLOW_ORIGINS=["*"]
    settings=_S()

# Use the minimal router that has ZERO third-party deps
from app.routes.health_smoketest import router as health_router

app = FastAPI(title=getattr(settings, "APP_NAME", "EchoScript API"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ALLOW_ORIGINS", ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=getattr(settings, "API_PREFIX", "/api"))