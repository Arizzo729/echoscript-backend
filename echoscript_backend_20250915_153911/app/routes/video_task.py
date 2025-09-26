# app/routes/video_task.py
import os
import tempfile
import time
from typing import Union

import ffmpeg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import config
from app.dependencies import get_current_user
from app.schemas.subtitle import SubtitleOut
from app.schemas.transcription import TranscriptionOut
from app.services.transcription import FasterWhisperTranscriber
from app.utils.logger import logger

# Initialize our faster-whisper service
_TRANSCRIBER = FasterWhisperTranscriber(model_name=os.getenv("ASR_MODEL", "large-v3"))

router = APIRouter()


def translate_text(text: str, target_lang: str) -> str:
    """Placeholder translation function. Replace with actual translation logic if needed."""
    logger.warning("translate_text() called, but no translation backend is configured.")
    return text


@router.post(
    "/",
    response_model=Union[TranscriptionOut, SubtitleOut],
    summary="Process uploaded video for transcription or subtitle generation",
)
async def video_task(
    file: UploadFile = File(..., description="Video or audio file to process"),
    task_type: str = Form(
        ...,
        regex="^(transcription|subtitles)$",
        description="Task: 'transcription' or 'subtitles'",
    ),
    subtitle_target: str | None = Form(
        None,
        description="ISO language code for translating subtitles (e.g., 'en', 'es')",
    ),
    translate_output: bool = Form(
        False,
        description="Whether to translate the output into the subtitle_target language",
    ),
    current_user=Depends(get_current_user),
) -> TranscriptionOut | SubtitleOut:
    """
    Accepts a video/audio upload and returns either a transcription or subtitles.

    - If `task_type` is 'transcription', returns raw text (optionally translated).
    - If `task_type` is 'subtitles', returns SRT-formatted subtitles (optionally translated).
    """
    suffix = os.path.splitext(file.filename or "")[1]
    tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    video_path = tmp_video.name
    audio_path = None

    try:
        tmp_video.write(await file.read())
        tmp_video.flush()
        tmp_video.close()

        # Extract audio as WAV (16kHz mono)
        audio_path = f"{video_path}.wav"
        try:
            ffmpeg.input(video_path).output(
                audio_path, format="wav", acodec="pcm_s16le", ac=1, ar="16000"
            ).run(quiet=True, overwrite_output=True)
        except ffmpeg.Error as e:
            logger.error(f"Audio extraction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract audio from video",
            )

        # Run faster-whisper transcription
        lang, segments = _TRANSCRIBER.transcribe(audio_path)

        transcript_text = " ".join(seg.text for seg in segments)

        if task_type == "subtitles":
            # Build SRT content
            lines = []
            for idx, seg in enumerate(segments, start=1):
                start = seg.start or 0.0
                end = seg.end or 0.0
                start_ts = time.strftime("%H:%M:%S", time.gmtime(start)) + ",000"
                end_ts = time.strftime("%H:%M:%S", time.gmtime(end)) + ",000"
                lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{seg.text}\n")
            subtitles_text = "\n".join(lines)
            if translate_output and subtitle_target:
                subtitles_text = translate_text(subtitles_text, subtitle_target)
            return SubtitleOut(
                subtitles=subtitles_text,
                language=subtitle_target or lang or config.DEFAULT_LANGUAGE,
                format="srt",
            )

        # task_type == transcription
        if translate_output and subtitle_target:
            transcript_text = translate_text(transcript_text, subtitle_target)

        return TranscriptionOut(
            transcript=transcript_text,
            summary=None,
            sentiment=None,
            keywords=None,
            subtitles=None,
        )

    finally:
        for path in (video_path, audio_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {path}: {e}")
