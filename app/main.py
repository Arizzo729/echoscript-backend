# Must be first: apply CRUDRouter Pydantic-v2 patch
import app.utils.crudrouter_patch

import os
import tempfile
import logging
import warnings
from datetime import datetime
from typing import Any, Optional

import torch
from fastapi import (
    FastAPI, UploadFile, File, WebSocket,
    HTTPException, Request, Depends, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from fastapi_crudrouter import SQLAlchemyCRUDRouter

from app.db import engine, Base, get_db
from app.config import Config, redis_client
from app.dependencies import get_current_user
from app.utils.safety_check import run_safety_checks
from app.utils.echo_ai import apply_gpt_cleanup

# Import ORM models to register tables
import app.models
from app.models import Item

# Routers
from app.routes.auth import router as auth_router
from app.routes.search import router as search_router
from app.routes.newsletter import router as newsletter_router
from app.routes.transcribe import router as transcribe_router
from app.routes.summary import router as summary_router
from app.routes.subscription import router as subscription_router
from app.routes.subscription import router as subscription_router
app.include_router(subscription_router, prefix="/api", tags=["subscription"])


# Schemas
from app.schemas import (
    ItemRead, ItemCreate, ItemUpdate,
    NewsletterSubscribeRequest, NewsletterSubscribeResponse,
    SubscriptionRead, SubscriptionCreate, SubscriptionUpdate,
)

# -------------------------------------------------------------------------
# Suppress non-critical warnings
# -------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=FutureWarning)

# -------------------------------------------------------------------------
# Logging configuration (UTF-8 safe)
# -------------------------------------------------------------------------
logging.root.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)
logging.root.addHandler(handler)
logging.root.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(Config.APP_NAME)

# -------------------------------------------------------------------------
# Initialize FastAPI
# -------------------------------------------------------------------------
app = FastAPI(
    title=Config.APP_NAME,
    description="Audio transcription, summarization & user management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# -------------------------------------------------------------------------
# CORS configuration
# -------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# Mount static directories
# -------------------------------------------------------------------------
for directory in (Config.UPLOAD_FOLDER, Config.EXPORT_DIR, Config.LOG_DIR):
    if os.path.isdir(directory):
        name = os.path.basename(directory)
        app.mount(f"/{name}", StaticFiles(directory=directory), name=name)

# Record startup time for uptime metrics
_start_time = datetime.utcnow()

# -------------------------------------------------------------------------
# Startup & Shutdown events
# -------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    run_safety_checks()
    Base.metadata.create_all(bind=engine)
    logger.info("[DB OK] Tables ensured")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[Startup] Device={device}, WhisperModel={Config.WHISPER_MODEL}")

@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("[Shutdown] API server shutting down")

# -------------------------------------------------------------------------
# Response models
# -------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    device: str
    model: str
    redis_connected: bool

class VersionResponse(BaseModel):
    version: str
    build_time: datetime

class MetricsResponse(BaseModel):
    uptime: float
    redis_connected: bool
    device: str
    model: str

class RedisTestResponse(BaseModel):
    redis: str
    value: str

# -------------------------------------------------------------------------
# Health & Info endpoints
# -------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HealthResponse(
        status="ok",
        device=device,
        model=Config.WHISPER_MODEL,
        redis_connected=bool(redis_client),
    )

@app.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(version=app.version, build_time=datetime.utcnow())

@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    return MetricsResponse(
        uptime=uptime,
        redis_connected=bool(redis_client),
        device="cuda" if torch.cuda.is_available() else "cpu",
        model=Config.WHISPER_MODEL,
    )

@app.get("/test-redis", response_model=RedisTestResponse)
def test_redis() -> RedisTestResponse:
    try:
        if not redis_client:
            raise RuntimeError("Redis client not configured")
        redis_client.setex("echoscript_ping", 30, "pong")
        raw = redis_client.get("echoscript_ping")
        val = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
        return RedisTestResponse(redis="connected", value=val or "")
    except Exception as exc:
        return RedisTestResponse(redis=f"error: {exc}", value="")

# -------------------------------------------------------------------------
# WhisperX model loader
# -------------------------------------------------------------------------
_whisper_model: Any = None

def load_whisper_model() -> Any:
    global _whisper_model
    if _whisper_model is None:
        import whisperx
        _whisper_model = whisperx.load_model(
            Config.WHISPER_MODEL,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        logger.info(f"[WhisperX OK] Loaded {Config.WHISPER_MODEL}")
    return _whisper_model

# -------------------------------------------------------------------------
# Transcription endpoint
# -------------------------------------------------------------------------
class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float

@app.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_201_CREATED
)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Config.DEFAULT_LANGUAGE,
    db: Any = Depends(get_db),
) -> TranscriptionResponse:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported file format")

    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        whisper = load_whisper_model()
        segments, info = whisper.transcribe(tmp_path, language=language, beam_size=5)
        raw = "\n".join(seg.text.strip() for seg in segments)

        try:
            cleaned = await apply_gpt_cleanup(raw)
        except Exception:
            cleaned = raw

        return TranscriptionResponse(
            transcript=cleaned,
            language=info.language or language,
            confidence=round(getattr(info, "confidence", 0.0), 2),
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# -------------------------------------------------------------------------
# WebSocket stub
# -------------------------------------------------------------------------
@app.websocket("/ws/transcribe")
async def ws_transcribe(ws: WebSocket):
    await ws.accept()
    await ws.send_text("Live transcription coming soon.")

# -------------------------------------------------------------------------
# CRUD router for Item model
# -------------------------------------------------------------------------
item_router = SQLAlchemyCRUDRouter(
    db_model=Item,
    db=get_db,
    schema=ItemRead,
    create_schema=ItemCreate,
    update_schema=ItemUpdate,
    prefix="items",
    tags=["items"],
)
app.include_router(item_router)

# -------------------------------------------------------------------------
# Include additional routers
# -------------------------------------------------------------------------
for router in (
    auth_router, search_router, newsletter_router,
    transcribe_router, summary_router, subscription_router
):
    app.include_router(router)

# -------------------------------------------------------------------------
# Global exception handlers
# -------------------------------------------------------------------------
@app.exception_handler(404)
async def handle_404(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error(f"[Unhandled ERROR] {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
