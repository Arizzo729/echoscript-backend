# app/routes/transcribe.py
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse

# Mount this router at /api/v1, so the final endpoint is:
#   POST /api/v1/transcribe?language=en
router = APIRouter(prefix="/api/v1", tags=["transcribe"])

@router.post("/transcribe")
async def transcribe_endpoint(
    language: str = Query("en"),
    file: UploadFile = File(...),
):
    # NOTE: this is a stub so we can verify end-to-end wiring.
    # Replace with your Whisper/Faster-Whisper handler later.
    # We don't read the whole file here to avoid memory spikes.
    return JSONResponse(
        {
            "ok": True,
            "filename": file.filename,
            "language": language,
            "text": "(transcription stub — backend is wired correctly)",
        }
    )
