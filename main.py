# === EchoScript.AI — main.py (Advanced Version) ===

from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
from starlette.responses import JSONResponse
from faster_whisper import WhisperModel
import tempfile, logging, os, torch

# === Local Imports ===
from app.db import engine, SessionLocal
from app import models
from app.routes import (
    signup, auth_password, verify_reset, send_reset_code, profile, stripe_webhooks
)
from app.utils.echo_ai import apply_gpt_cleanup

# === Load .env ===
load_dotenv()
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echoscript")

# === App Initialization ===
app = FastAPI()

# === CORS Setup ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Database Initialization ===
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Load Whisper Model ===
logger.info(f"Loading Whisper model '{WHISPER_MODEL}' on {DEVICE} ({COMPUTE_TYPE})")
try:
    model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
    logger.info("Whisper model loaded successfully.")
except Exception as e:
    logger.exception("Model failed to load:")
    raise RuntimeError(f"Whisper model initialization failed: {e}")

# === Health Check ===
@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE}

# === Transcription Request Schema ===
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
        logging.info("1: File received")

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        logging.info("2: File saved to temp")

        segments, info = model.transcribe(tmp_path, language=language, beam_size=5)
        raw_transcript = "\n".join([seg.text.strip() for seg in segments])

        logging.info("3: Raw transcription complete")

        # === Apply Echo AI Cleanup ===
        enhanced_transcript = await apply_gpt_cleanup(text=raw_transcript)

        logging.info("4: Enhanced transcript generated")

        return TranscriptionResponse(
            transcript=enhanced_transcript,
            language=info.language or language,
            confidence=0.95
        )

    except Exception as e:
        logging.exception("Transcription failed with exception:")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# === WebSocket Placeholder ===
@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Live transcription coming soon.")

# === Stripe Webhook ===
app.include_router(stripe_webhooks.router)

# === Auth & Profile Routes ===
app.include_router(signup.router)
app.include_router(auth_password.router)
app.include_router(verify_reset.router)
app.include_router(send_reset_code.router)
app.include_router(profile.router)

# === Global Exception Handler ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})


