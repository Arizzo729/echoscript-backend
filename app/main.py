# === app/main.py — EchoScript.AI: Hardened, Modular, Production-Grade API ===

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
from starlette.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Any

# === Ignore noisy deprecation warnings ===
warnings.filterwarnings("ignore", category=FutureWarning)

# === Load env vars and configs ===
load_dotenv()

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL    = os.getenv("WHISPER_MODEL", "medium")
DEVICE           = "cuda" if torch.cuda.is_available() else "cpu"

# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("echoscript")

# === App ===
app = FastAPI(
    title="EchoScript.AI API",
    description="Audio transcription, summarization & user management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# === CORS for all origins, secured ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Serve static directories in dev ===
for static_dir in ("static", "exports", "logs"):
    path = os.path.join(os.path.dirname(__file__), static_dir)
    if os.path.isdir(path):
        app.mount(f"/{static_dir}", StaticFiles(directory=path), name=static_dir)

# === Safe imports & dependency checks ===
try:
    from .config import config, redis_client
    from .utils.safety_check import run_safety_checks
    from .db import engine, get_db
    from .models import Base
    from .routes.auth         import router as auth_router
    from .routes.search       import router as search_router
    from .routes.newsletter   import router as newsletter_router
    from .routes.transcribe   import router as transcribe_router
    from .routes.summary      import router as summary_router
    from .routes.subscription import router as subscription_router
    from .utils.echo_ai       import apply_gpt_cleanup
    from .utils.gpt_logic     import summarize_transcript
except ImportError as e:
    logger.critical(f"[Import ❌] Startup import failure: {e}")
    raise

# === Global startup checks (env, Redis, DB, keys) ===
@app.on_event("startup")
def on_startup():
    run_safety_checks()
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[DB ✅] Tables checked/created.")
    except Exception as e:
        logger.error(f"[DB ❌] Table initialization failed: {e}")
        raise

    logger.info(f"[Startup] Running on device={DEVICE}, model={WHISPER_MODEL}")

# === Simple Prometheus/monitoring endpoint ===
@app.get("/metrics")
def metrics() -> dict:
    return {
        "uptime": (datetime.utcnow() - datetime.fromtimestamp(os.getpid())).total_seconds(),
        "redis_connected": bool(redis_client),
        "device": DEVICE,
        "model": WHISPER_MODEL,
    }

# === Healthcheck ===
@app.get("/health", response_model=dict)
def health() -> dict:
    return {
        "status":           "ok",
        "device":           DEVICE,
        "model":            WHISPER_MODEL,
        "redis_connected":  bool(redis_client),
    }

# === API version endpoint ===
@app.get("/version", response_model=dict)
def version() -> dict:
    return {
        "version": app.version,
        "build_time": datetime.utcnow().isoformat() + "Z"
    }

# === Redis test endpoint ===
@app.get("/test-redis", response_model=dict)
def test_redis() -> dict:
    if not redis_client:
        return {"redis": "not connected"}
    try:
        redis_client.setex("echoscript_ping", 30, "pong")
        return {"redis": "connected", "value": redis_client.get("echoscript_ping")}
    except Exception as e:
        return {"redis": f"error: {e}"}

# === Model Loader: ensures model loads only once per worker ===
_whisper_model = None

def load_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisperx
            _whisper_model = whisperx.load_model(WHISPER_MODEL, device=DEVICE)
            logger.info(f"✅ WhisperX model loaded: {WHISPER_MODEL} on {DEVICE}")
        except Exception as e:
            logger.critical(f"Whisper model failed to load: {e}")
            raise
    return _whisper_model

# === Response schemas ===
class TranscriptionResponse(BaseModel):
    transcript: str
    language:   str
    confidence: float

# === Core Transcription Endpoint ===
@app.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
)
async def transcribe_audio(
    file:      UploadFile = File(...),
    language:  str        = DEFAULT_LANGUAGE,
    db: Any    = Depends(get_db),
) -> TranscriptionResponse:
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

        whisper = load_model()
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

# === WebSocket placeholder (can swap for full streaming later) ===
@app.websocket("/ws/transcribe")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("🔊 Live transcription coming soon.")

# === Router registration (no double prefixing) ===
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(newsletter_router)
app.include_router(transcribe_router)
app.include_router(summary_router)
app.include_router(subscription_router)

# === 404 Not Found Handler ===
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Not found"})

# === Global Validation Error Handler ===
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# === Global Exception Handler (logs stack trace) ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger.error(f"[Unhandled Exception] {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "trace": traceback.format_exc(),
        }
    )

# === Custom shutdown logic (log, notify, flush, etc) ===
@app.on_event("shutdown")
def on_shutdown():
    logger.info("[Shutdown] API server shutting down.")
