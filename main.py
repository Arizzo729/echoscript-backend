from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
import tempfile
import subprocess
import uuid

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "auto")  # auto-detect by default

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response schema
class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float

# POST route for audio transcription
@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    if not file.filename.endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4", ".mov")):
        raise HTTPException(status_code=415, detail="Unsupported file format")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # Example: whisper.cpp / local whisper call
        whisper_command = [
            "whisper",
            tmp_path,
            "--language", DEFAULT_LANGUAGE,
            "--output_format", "txt",
            "--model", "large-v3"  # For extremely difficult/multilingual audio
        ]
        subprocess.run(whisper_command, check=True)

        txt_file = tmp_path + ".txt"
        with open(txt_file, "r", encoding="utf-8") as f:
            transcript = f.read().strip()

        # Fake confidence and language detection for now
        return {
            "transcript": transcript,
            "language": DEFAULT_LANGUAGE,
            "confidence": 0.95
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        try:
            os.remove(tmp_path)
            os.remove(txt_file)
        except:
            pass

# WebSocket route for live transcription
@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        buffer = b""
        while True:
            chunk = await websocket.receive_bytes()
            buffer += chunk

            if len(buffer) > 500000:  # ~0.5 MB chunks
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(buffer)
                    tmp_path = tmp.name

                # Simulated live response
                await websocket.send_text("Partial transcript placeholder")
                buffer = b""
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")

