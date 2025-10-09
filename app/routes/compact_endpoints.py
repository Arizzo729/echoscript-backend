# app/routes/compat_endpoints.py
"""
Compatibility endpoints for legacy frontend calls.

Exposes:
  - POST /api/video/process
  - POST /api/v1/transcribe
  - POST /v1/transcribe

If the real transcription stack is available, we try to use it.
Otherwise, we return a harmless stub so the UI can proceed without 404s.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Compat"])

# Try optional real transcriber if your code provides one.
# Adjust these imports to your actual service modules if needed.
try:
    from app.routes.video_task import process_media_file  # type: ignore
    HAVE_VIDEO_TASK = True
except Exception:
    process_media_file = None  # type: ignore
    HAVE_VIDEO_TASK = False

try:
    # Optional example: your FasterWhisper service, if present
    from app.services.transcription import FasterWhisperTranscriber  # type: ignore
    HAVE_WHISPER = True
except Exception:
    FasterWhisperTranscriber = None  # type: ignore
    HAVE_WHISPER = False


def _save_temp(upload: UploadFile) -> str:
    suffix = os.path.splitext(upload.filename or "upload")[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload.file.read())
        return tmp.name


def _cleanup(path: str) -> None:
    try:
        os.remove(path)
    except Exception:
        pass


@router.post("/api/video/process")
async def compat_video_process(
    file: UploadFile = File(...),
    task_type: Optional[str] = Form("transcription"),
    language: Optional[str] = Form("en"),
):
    """
    Compatibility for frontend expecting /api/video/process.
    If your real video_task pipeline exists, use it; otherwise return a stub.
    """
    src = _save_temp(file)
    try:
        if HAVE_VIDEO_TASK and callable(process_media_file):
            # Delegate to your actual media pipeline (sync call expected)
            result = process_media_file(src, task_type=task_type or "transcription", language=language or "en")  # type: ignore
            return JSONResponse(status_code=200, content=result if isinstance(result, dict) else {"ok": True, "result": result})
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "task_type": task_type or "transcription",
                    "language": language or "en",
                    "text": "",
                    "note": "Compat endpoint active; real media pipeline not wired in this deployment.",
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"video/process failed: {e}")
    finally:
        _cleanup(src)


# We expose both /api/v1/transcribe and /v1/transcribe to cover all callers.
@router.post("/api/v1/transcribe")
@router.post("/v1/transcribe")
async def compat_transcribe_v1(
    file: UploadFile = File(...),
    language: Optional[str] = "en",
):
    """
    Compatibility for frontend expecting /v1/transcribe (or /api/v1/transcribe).
    If Whisper stack exists, use it; else return a stub.
    """
    src = _save_temp(file)
    try:
        if HAVE_WHISPER and FasterWhisperTranscriber:
            transcriber = FasterWhisperTranscriber()  # type: ignore[call-arg]
            # Adjust to your API: use whatever method returns text from file path
            text = transcriber.transcribe_text(src, language=language or "en")  # type: ignore[attr-defined]
            return {"text": text, "language": language or "en"}
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "text": "",
                    "language": language or "en",
                    "note": "Compat endpoint active; Whisper not enabled on this deployment.",
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"transcribe failed: {e}")
    finally:
        _cleanup(src)
