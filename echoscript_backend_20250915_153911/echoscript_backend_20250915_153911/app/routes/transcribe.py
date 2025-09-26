# app/routes/transcribe.py
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user
from app.services.transcription import FasterWhisperTranscriber

router = APIRouter(prefix="/api/v1", tags=["Transcription"])

# Use a lighter model by default for local dev; override with ASR_MODEL in .env
_TRANSCRIBER = FasterWhisperTranscriber(model_name=os.getenv("ASR_MODEL", "base"))


@router.post("/transcribe")
async def transcribe_endpoint(
    file: UploadFile = File(...),
    diarize: bool = False,
    language: str | None = None,
    vad: bool = True,  # on by default; will auto-fallback if onnxruntime missing
    user=Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix or ".wav"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Try with VAD; if onnxruntime is missing, retry without it automatically.
        try:
            lang, segs = _TRANSCRIBER.transcribe(tmp_path, language=language, vad=vad)
        except Exception as e:
            msg = str(e)
            if "onnxruntime" in msg or "VAD filter requires" in msg:
                lang, segs = _TRANSCRIBER.transcribe(
                    tmp_path, language=language, vad=False
                )
            else:
                raise

        if diarize:
            turns = _TRANSCRIBER.diarize(
                tmp_path
            )  # returns [] if pyannote not installed
            segs = _TRANSCRIBER.assign_speakers(segs, turns)

        return JSONResponse(
            {
                "language": lang,
                "segments": [
                    {
                        "start": round(s.start, 2),
                        "end": round(s.end, 2),
                        "text": s.text,
                        "speaker": s.speaker,
                    }
                    for s in segs
                ],
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
