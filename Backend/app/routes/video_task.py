import os
import tempfile
import time
from typing import Optional, Union

import ffmpeg  # type: ignore[attr-defined]
import torch  # type: ignore[attr-defined]
import whisperx  # type: ignore[attr-defined]
from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)

from app.config import config
from app.dependencies import get_current_user
from app.schemas.subtitle import SubtitleOut
from app.schemas.transcription import TranscriptionOut
from app.utils.gpt_logic import translate_text
from app.utils.logger import logger

# Preload WhisperX model and alignment for transcription
device = "cuda" if torch.cuda.is_available() else "cpu"
whisper_model = whisperx.load_model(
    config.WHISPER_MODEL, device=device, compute_type="float32"
)
align_model, align_metadata = whisperx.load_align_model(
    language_code=config.DEFAULT_LANGUAGE, device=device
)

router = APIRouter()


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
    subtitle_target: Optional[str] = Form(
        None,
        description="ISO language code for translating subtitles (e.g., 'en', 'es')",
    ),
    translate_output: bool = Form(
        False,
        description="Whether to translate the output into the subtitle_target language",
    ),
    current_user=Depends(get_current_user),
) -> Union[TranscriptionOut, SubtitleOut]:
    """
    Accepts a video/audio upload and returns either a transcription or subtitles.

    - If `task_type` is 'transcription', returns raw text (optionally translated).
    - If `task_type` is 'subtitles', returns SRT-formatted subtitles (optionally translated).
    """
    # Save upload to a temporary file
    suffix = os.path.splitext(file.filename or "")[1]
    tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp_video.write(await file.read())
        tmp_video.flush()
        tmp_video.close()
        video_path = tmp_video.name

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

        # Transcribe audio with WhisperX and align timestamps
        result = whisperx.transcribe(
            whisper_model,
            audio_path,
            batch_size=16,
            device=device,
            return_timestamps=True,
        )
        result = whisperx.align(
            result.get("segments", []),
            audio_path,
            align_model,
            align_metadata,
            device=device,
        )
        transcript_text = " ".join(seg.get("text", "") for seg in result)

        if task_type == "subtitles":
            # Build SRT content
            lines = []
            for idx, seg in enumerate(result, start=1):
                start = seg.get("start", 0.0)
                end = seg.get("end", 0.0)
                start_ts = time.strftime("%H:%M:%S", time.gmtime(start)) + ",000"
                end_ts = time.strftime("%H:%M:%S", time.gmtime(end)) + ",000"
                lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{seg.get('text','')}\n")
            subtitles_text = "\n".join(lines)
            if translate_output and subtitle_target:
                subtitles_text = translate_text(subtitles_text, subtitle_target)
            return SubtitleOut(
                subtitles=subtitles_text,
                language=subtitle_target or config.DEFAULT_LANGUAGE,
                format="srt",
            )

        # task_type == transcription
        if translate_output and subtitle_target:
            transcript_text = translate_text(transcript_text, subtitle_target)

        # Return transcription with empty optional fields
        return TranscriptionOut(
            transcript=transcript_text,
            summary=None,
            sentiment=None,
            keywords=None,
            subtitles=None,
        )

    finally:
        # Clean up temporary files
        for path in (video_path, audio_path):  # type: ignore[name-defined]
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.warning(f"Could not remove temp file {path}: {e}")
