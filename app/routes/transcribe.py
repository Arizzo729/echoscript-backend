# app/routes/transcribe.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
import os, requests

router = APIRouter(prefix="/api/v1", tags=["transcribe"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1").strip()

@router.post("/transcribe")
async def transcribe_endpoint(
    language: str = Query("en"),
    file: UploadFile = File(...),
):
    """
    Uses OpenAI Whisper (server-side) to transcribe the uploaded file.
    Expects: multipart/form-data with 'file'
    Returns: { ok, filename, language, text }
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured on the backend")

    try:
        # Ensure we read from the start
        file.file.seek(0)

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
        data = {
            "model": OPENAI_WHISPER_MODEL,  # "whisper-1"
            "language": language,
            "response_format": "json",
        }
        files = {
            "file": (file.filename, file.file, file.content_type or "application/octet-stream")
        }

        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            data=data,
            files=files,
            timeout=600,
        )
        if resp.status_code != 200:
            # Bubble up OpenAI’s error for easier debugging
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        text = resp.json().get("text", "")

        return JSONResponse(
            {
                "ok": True,
                "filename": file.filename,
                "language": language,
                "text": text,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
