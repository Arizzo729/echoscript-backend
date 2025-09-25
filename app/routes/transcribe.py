# app/routes/transcribe.py
import os
import shutil
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1", tags=["transcription"])

DEMO = os.getenv("DEMO_TRANSCRIBE", "1") == "1"
_model = None  # singleton model


def _get_model():
    """Create/reuse a CPU-friendly faster-whisper model."""
    global _model
    if _model is not None:
        return _model

    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    os.environ.setdefault("ORT_DISABLE_GPU", "1")

    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "faster-whisper import failed. Install deps:\n"
            "  pip install faster-whisper ctranslate2 tokenizers sentencepiece numpy\n"
            f"Original error: {e}"
        )

    model_name = os.getenv("ASR_MODEL", "base.en")
    compute_type = os.getenv("ASR_COMPUTE_TYPE", "int8")
    try:
        _model = WhisperModel(model_name, device="cpu", compute_type=compute_type)
    except Exception:
        _model = WhisperModel(model_name, device="cpu", compute_type="int16")
    return _model


@router.post("/transcribe/warmup")
def warmup():
    if DEMO:
        return {"ok": True, "mode": "demo"}
    _ = _get_model()
    return {"ok": True, "mode": "real"}


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    diarize: Optional[bool] = False,
    vad: Optional[bool] = False,
    language: Optional[str] = "en",
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    tmp_path = os.path.join(
        tempfile.gettempdir(), f"echoscript_{uuid.uuid4().hex}.{ext}"
    )
    with open(tmp_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    if DEMO:
        return JSONResponse(
            {
                "filename": file.filename,
                "tmp_path": tmp_path,
                "language": language,
                "diarize": bool(diarize),
                "vad": bool(vad),
                "text": f"(demo) Received '{file.filename}', diarize={bool(diarize)}, vad={bool(vad)}, lang={language}.",
            }
        )

    try:
        model = _get_model()
        segments, info = model.transcribe(
            tmp_path, language=language or None, vad_filter=bool(vad)
        )
        text = "".join(seg.text for seg in segments)
        return JSONResponse(
            {
                "filename": file.filename,
                "language": (language or info.language or "en"),
                "diarize": False,
                "vad": bool(vad),
                "text": text,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
