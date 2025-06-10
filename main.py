from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
import tempfile
import logging
import whisperx
import shutil

# ==== Load environment ====
load_dotenv()
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = "cuda" if shutil.which("nvidia-smi") else "cpu"

# ==== App setup ====
app = FastAPI()

# ==== CORS ====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== Logging ====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== Response Schema ====
class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float

# ==== WhisperX Model Load ====
logger.info(f"Loading WhisperX model: {WHISPER_MODEL} on {DEVICE}")
model = whisperx.load_model(WHISPER_MODEL, device=DEVICE)

# ==== POST: Transcription ====
@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".mov")):
        raise HTTPException(status_code=415, detail="Unsupported file format")

    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Run whisperx
        logger.info(f"Transcribing file: {file.filename}")
        result = model.transcribe(tmp_path, batch_size=16, language=DEFAULT_LANGUAGE)

        transcript = "\n".join([seg["text"].strip() for seg in result["segments"]])
        return TranscriptionResponse(
            transcript=transcript,
            language=result.get("language", DEFAULT_LANGUAGE),
            confidence=0.95  # WhisperX does not return direct confidence, can be enhanced later
        )

    except Exception as e:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# ==== WebSocket (optional placeholder) ====
@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Live transcription not implemented yet.")

