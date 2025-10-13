# app/routes/video_task.py
import os
import tempfile
from typing import Optional, Union

import ffmpeg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.settings import settings
from app.dependencies import get_current_active_user
from app.schemas.subtitle import SubtitleOut
from app.schemas.transcription import TranscriptionOut
from app.services.transcription import FasterWhisperTranscriber
from app.utils.logger import logger

router = APIRouter(prefix="/video-task", tags=["Transcription"])

# Initialize the transcriber once, using settings
# This will be reused across all requests to this route
_TRANSCRIBER = FasterWhisperTranscriber(
    model_name=settings.WHISPER_MODEL_SIZE,
    compute_type=settings.WHISPER_COMPUTE
)

@router.post("/", response_model=Union[TranscriptionOut, SubtitleOut])
async def process_video_task(
    file: UploadFile = File(...),
    task_type: str = Form("transcription", description="'transcription' or 'subtitles'"),
    language: Optional[str] = Form(None),
    current_user = Depends(get_current_active_user),
):
    """
    Processes a video or audio file to perform transcription or generate subtitles.

    - Extracts audio from the uploaded file using ffmpeg.
    - Uses FasterWhisper to transcribe the audio.
    - Returns either the full transcript or subtitles in SRT format.
    """
    if task_type not in {"transcription", "subtitles"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task_type")

    suffix = os.path.splitext(file.filename or "upload.bin")[-1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_media_file:
        tmp_media_file.write(await file.read())
        tmp_media_path = tmp_media_file.name

    wav_path = tmp_media_path + ".wav"

    try:
        # Use ffmpeg to convert the uploaded file to a standardized WAV format
        (
            ffmpeg.input(tmp_media_path)
            .output(wav_path, ac=1, ar=16000, format="wav") # 16kHz, mono
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )

        if task_type == "transcription":
            lang, segments = _TRANSCRIBER.transcribe(wav_path, language=language)
            full_text = " ".join(s.text for s in segments).strip()
            return TranscriptionOut(transcript=full_text)
        else: # subtitles
            # This is a placeholder for SRT generation. 
            # A proper implementation would format the segments from the transcribe method.
            lang, segments = _TRANSCRIBER.transcribe(wav_path, language=language)
            srt_content = to_srt(segments)
            return SubtitleOut(subtitles=srt_content, language=lang, format="srt")

    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        raise HTTPException(status_code=500, detail="Failed to process media file.")
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform transcription.")
    finally:
        # Clean up temporary files
        if os.path.exists(tmp_media_path):
            os.remove(tmp_media_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

def to_srt(segments):
    """Helper function to convert segments to SRT format."""
    def format_time(sec: float) -> str:
        h, rem = divmod(sec, 3600)
        m, rem = divmod(rem, 60)
        s, ms = divmod(rem, 1)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int(ms*1000):03}"

    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{format_time(seg.start)} --> {format_time(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)