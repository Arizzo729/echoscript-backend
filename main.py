# === EchoScript.AI — main.py (Resilient & Modular) ===

from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile, logging, os, torch

# === Load .env ===
load_dotenv()
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echoscript")

# === FastAPI App Init ===
app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Import Internals Safely ===
try:
    from app.db import engine, SessionLocal
    from app import models
    from app.routes import (
        signup, auth_password, verify_reset, send_reset_code, profile, stripe_webhooks
    )
    from app.utils.echo_ai import apply_gpt_cleanup
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    raise

# === Create Tables ===
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error(f"Database setup failed: {e}")
    raise

# === DB Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Lazy Model Load ===
model = None
def load_model():
    global model
    if model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Whisper model '{WHISPER_MODEL}' on {DEVICE} ({COMPUTE_TYPE})...")
            model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.exception("Failed to load Whisper model.")
            raise RuntimeError(f"Whisper model load failed: {e}")
    return model

# === Health Check ===
@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE}

# === Response Model ===
class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float

# === Transcription Endpoint ===
@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".mov")):
        raise HTTPException(status_code=415, detail="Unsupported file format")

    tmp_path = None
    try:
        logger.info("1: File received")

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        logger.info("2: File saved to temp")

        whisper = load_model()
        segments, info = whisper.transcribe(tmp_path, language=language, beam_size=5)
        raw_transcript = "\n".join([seg.text.strip() for seg in segments])
        logger.info("3: Raw transcription complete")

        try:
            enhanced_transcript = await apply_gpt_cleanup(text=raw_transcript)
            logger.info("4: GPT cleanup applied")
        except Exception as gpt_err:
            logger.warning(f"GPT cleanup failed: {gpt_err}")
            enhanced_transcript = raw_transcript

        return TranscriptionResponse(
            transcript=enhanced_transcript,
            language=info.language or language,
            confidence=0.95
        )

    except Exception as e:
        logger.exception("Transcription failed:")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# === Video Upload Placeholder ===
@app.post("/video-upload")
async def video_upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
        raise HTTPException(status_code=415, detail="Unsupported video format")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        logger.info(f"Video file saved: {tmp_path}")
        # TODO: Extract audio and transcribe

        return {"status": "success", "filename": file.filename}

    except Exception as e:
        logger.exception("Video upload failed:")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# === WebSocket Stub ===
@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Live transcription coming soon.")

# === Include All Routers ===
app.include_router(signup.router)
app.include_router(auth_password.router)
app.include_router(verify_reset.router)
app.include_router(send_reset_code.router)
app.include_router(profile.router)
app.include_router(stripe_webhooks.router)

# === Global Error Handler ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})

