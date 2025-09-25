# app/routes/video_task.py
import os
import tempfile
from typing import Optional, Union

import ffmpeg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import config
from app.dependencies import get_current_user
from app.schemas.subtitle import SubtitleOut
from app.schemas.transcription import TranscriptionOut
from app.services.transcription import FasterWhisperTranscriber
from app.utils.logger import logger

router = APIRouter(prefix="/api/video", tags=["Video Tasks"])

_TRANSCRIBER = FasterWhisperTranscriber(model_name=os.getenv("ASR_MODEL", "base"))


@router.post("/process", response_model=Union[TranscriptionOut, SubtitleOut])
async def process_video(
    file: UploadFile = File(...),
    task_type: str = Form(..., description="transcription|subtitles"),
    language: Optional[str] = Form("en"),
    translate_output: bool = Form(False),
    current_user=Depends(get_current_user),
):
    if task_type not in {"transcription", "subtitles"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task_type"
        )

    suffix = os.path.splitext(file.filename or "upload.bin")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Normalize audio with ffmpeg to WAV for stable inference
        wav_path = tmp_path + ".wav"
        (
            ffmpeg.input(tmp_path)
            .output(
                wav_path, ac=1, ar=config.WHISPER_SAMPLE_RATE or 16000, format="wav"
            )
            .overwrite_output()
            .run(quiet=True)
        )

        if task_type == "transcription":
            text = _TRANSCRIBER.transcribe_file(wav_path, language=language or "en")
            return TranscriptionOut(
                transcript=text,
                summary=None,
                sentiment=None,
                keywords=None,
                subtitles=None,
            )
        else:
            srt = _TRANSCRIBER.transcribe_to_srt(wav_path, language=language or "en")
            return SubtitleOut(subtitles=srt, language=language or "en", format="srt")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing failed",
        )
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        try:
            os.remove(wav_path)
        except Exception:
            pass
