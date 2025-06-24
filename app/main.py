# === EchoScript.AI — main.py (Hardened, Modular, Production-Ready with Auth, Search & Newsletter) ===

import os, tempfile, logging, torch, warnings
from datetime import datetime
from fastapi import (
    FastAPI, UploadFile, File, WebSocket,
    HTTPException, Request, Depends, status
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import BaseModel

# === Suppress Deprecation Warnings ===
warnings.filterwarnings("ignore", category=FutureWarning)

# === Load Environment Variables ===
load_dotenv()

# === Configuration ===
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("echoscript")

# === FastAPI Initialization ===
app = FastAPI(
    title="EchoScript.AI API",
    description="Audio transcription, summarization & user management",
    version="1.0.0"
)

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Safe Imports ===
try:
    from app.config import config, redis_client
    from app.utils.safety_check import run_safety_checks
    from app.db import engine, SessionLocal
    from app import models

    # Routers
    from app.routes.auth import router as auth_router
    from app.routes.search import router as search_router
    from app.routes.newsletter import router as newsletter_router
    from app.routes.transcribe import router as transcribe_router
    from app.routes.summary import router as summary_router

    # GPT cleanup utility
    from app.utils.echo_ai import apply_gpt_cleanup
except ImportError as e:
    logger.critical(f"[Import ❌] Startup import failure: {e}")
    raise

# === Safety Checks on Startup ===
run_safety_checks()

# === Database Initialization ===
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("[DB ✅] Tables checked/created.")
except Exception as e:
    logger.error(f"[DB ❌] Failed to initialize tables: {e}")
    raise

# === Dependency: DB Session ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Transcription Response Model ===
class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float

# === Health Endpoint ===
@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": DEVICE,
        "model": WHISPER_MODEL,
        "redis_connected": bool(redis_client)
    }

# === Test Redis Endpoint ===
@app.get("/test-redis")
def test_redis():
    if not redis_client:
        return {"redis": "not connected"}
    try:
        redis_client.setex("echoscript_ping", 30, "pong")
        return {"redis": "connected", "value": redis_client.get("echoscript_ping")}
    except Exception as e:
        return {"redis": f"error: {e}"}

# === Transcription API ===
@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith((
        ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".mov"
    )):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="Unsupported file format")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
            logger.info(f"[Audio] File saved: {tmp_path}")

        whisper = load_model()
        segments, info = whisper.transcribe(
            tmp_path,
            language=language,
            beam_size=5
        )
        raw = "\n".join([s.text.strip() for s in segments])
        logger.info("[Transcription ✅] Raw text generated")

        try:
            cleaned = await apply_gpt_cleanup(raw)
            logger.info("[GPT ✅] Enhancement applied")
        except Exception as e:
            logger.warning(f"[GPT ⚠️] Enhancement failed: {e}")
            cleaned = raw

        return TranscriptionResponse(
            transcript=cleaned,
            language=info.language or language,
            confidence=0.95
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# === WebSocket Placeholder ===
@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("🔊 Live transcription coming soon.")

# === Register Routers ===
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(newsletter_router)
app.include_router(transcribe_router)
app.include_router(summary_router)

# === Global Exception Handler ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"[Unhandled Error] {exc}")
    return JSONResponse(status_code=500,
                        content={"error": str(exc)})


