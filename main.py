from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import whisperx
import tempfile
import logging
import shutil
import os
import torch

# === Load .env ===
load_dotenv()
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# === Setup Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echoscript")

# === FastAPI App ===
app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# === Health Check ===
@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE}

# === Model Load ===
logger.info(f"Loading WhisperX model '{WHISPER_MODEL}' on '{DEVICE}' with '{COMPUTE_TYPE}'")
try:
    model = whisperx.load_model(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise RuntimeError("Model failed to load during startup.")

# === Schema ===
class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float

# === POST: Transcribe ===
@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...), language: str = DEFAULT_LANGUAGE):
    if not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".mov")):
        raise HTTPException(status_code=415, detail="Unsupported file format")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        logger.info(f"Transcribing file: {file.filename}")
        result = model.transcribe(tmp_path, batch_size=16, language=language)

        transcript = "\n".join([seg["text"].strip() for seg in result["segments"]])
        return TranscriptionResponse(
            transcript=transcript,
            language=result.get("language", language),
            confidence=0.95
        )
    except Exception as e:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# === WebSocket (placeholder) ===
@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Live transcription coming soon.")


