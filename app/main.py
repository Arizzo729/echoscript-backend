# === app/main.py — Hardened, Modular, Production-Ready with Auth, Search & Newsletter ===

import os
import tempfile
import logging
import torch
import warnings
from datetime import datetime
from fastapi import (
    FastAPI, UploadFile, File, WebSocket,
    HTTPException, Request, Depends, status
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Suppress noisy deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Load env vars
load_dotenv()

# Config
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL    = os.getenv("WHISPER_MODEL", "medium")
DEVICE           = "cuda" if torch.cuda.is_available() else "cpu"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("echoscript")

# FastAPI init
app = FastAPI(
    title="EchoScript.AI API",
    description="Audio transcription, summarization & user management",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Safe imports
try:
    from app.config import config, redis_client
    from app.utils.safety_check import run_safety_checks
    from app.db import engine, get_db              # use our centralized DB utils
    from app.models import Base                    # single Base from models package

    # Routers
    from app.routes.auth       import router as auth_router
    from app.routes.search     import router as search_router
    from app.routes.newsletter import router as newsletter_router
    from app.routes.transcribe import router as transcribe_router
    from app.routes.summary    import router as summary_router
    from app.routes.subscription import router as subscription_router

    # GPT cleanup util
    from app.utils.echo_ai    import apply_gpt_cleanup

except ImportError as e:
    logger.critical(f"[Import ❌] Startup import failure: {e}")
    raise

# Startup safety checks
run_safety_checks()

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("[DB ✅] Tables checked/created.")
except Exception as e:
    logger.error(f"[DB ❌] Failed to initialize tables: {e}")
    raise

# Transcription response schema
class TranscriptionResponse(BaseModel):
    transcript: str
    language:   str
    confidence: float

# Health
@app.get("/health")
def health():
    return {
        "status":           "ok",
        "device":           DEVICE,
        "model":            WHISPER_MODEL,
        "redis_connected":  bool(redis_client),
    }

# Redis test
@app.get("/test-redis")
def test_redis():
    if not redis_client:
        return {"redis": "not connected"}
    try:
        redis_client.setex("echoscript_ping", 30, "pong")
        return {"redis": "connected", "value": redis_client.get("echoscript_ping")}
    except Exception as e:
        return {"redis": f"error: {e}"}

# Transcription endpoint
@app.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
)
async def transcribe_audio(
    file:      UploadFile = File(...),
    language:  str        = DEFAULT_LANGUAGE,
    db=Depends(get_db),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".mov"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format"
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
            logger.info(f"[Audio] Saved to {tmp_path}")

        whisper = load_model()  # ensure you've defined load_model() in your utils
        segments, info = whisper.transcribe(tmp_path, language=language, beam_size=5)
        raw = "\n".join(s.text.strip() for s in segments)
        logger.info("[Transcription ✅] Raw text generated")

        try:
            cleaned = await apply_gpt_cleanup(raw)
            logger.info("[GPT ✅] Enhancement applied")
        except Exception as e:
            logger.warning(f"[GPT ⚠️] Enhancement failed: {e}")
            cleaned = raw

        return TranscriptionResponse(
            transcript= cleaned,
            language=   info.language or language,
            confidence= 0.95,
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# WebSocket placeholder
@app.websocket("/ws/transcribe")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("🔊 Live transcription coming soon.")

# Register routers
app.include_router(auth_router,       prefix="/api/auth")
app.include_router(search_router,     prefix="/api/search")
app.include_router(newsletter_router, prefix="/api/newsletter")
app.include_router(transcribe_router, prefix="/api/transcribe")
app.include_router(summary_router,    prefix="/api/summary")
app.include_router(subscription_router, prefix="/api/subscription")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"[Unhandled] {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})
tr(exc)})

