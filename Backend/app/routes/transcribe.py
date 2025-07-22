import os
import tempfile
from pathlib import Path
from typing import Optional

import ffmpeg  # type: ignore
import torch
import whisperx  # type: ignore
from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)

from app.config import config
from app.dependencies import get_current_user
from app.schemas.transcription import TranscriptionOut
from app.utils.gpt_logic import (analyze_sentiment, extract_keywords,
                                 summarize_transcript)
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
    response_model=TranscriptionOut,
    summary="Transcribe an audio/video file into text with AI enhancements",
)
async def transcribe(
    file: UploadFile = File(..., description="Audio or video file to transcribe"),
    generate_summary: bool = Form(
        False, description="Generate a summary of the transcript"
    ),
    generate_sentiment: bool = Form(
        False, description="Analyze sentiment of the transcript"
    ),
    generate_keywords: bool = Form(
        False, description="Extract keywords from the transcript"
    ),
    current_user=Depends(get_current_user),
) -> TranscriptionOut:
    """
    Transcribe the provided file using WhisperX and optionally generate summary,
    sentiment label, and keywords via GPT.
    """
    # Save upload to temp file
    filename = file.filename or ""
    suffix = os.path.splitext(filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        data = await file.read()
        tmp.write(data)
        tmp.flush()
        tmp.close()
        input_path = tmp.name

        # Extract audio to WAV (16kHz mono)
        audio_path = f"{input_path}.wav"
        try:
            ffmpeg.input(input_path).output(
                audio_path, format="wav", acodec="pcm_s16le", ac=1, ar="16000"
            ).run(quiet=True, overwrite_output=True)
        except ffmpeg.Error as e:
            logger.error(f"Audio extraction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract audio from file",
            )

        # Transcribe with WhisperX
        result = whisperx.transcribe(
            whisper_model,
            audio_path,
            batch_size=16,
            device=device,
            return_timestamps=False,
        )
        transcript_text = " ".join(seg["text"] for seg in result)

        # Optional AI enhancements
        summary = summarize_transcript(transcript_text) if generate_summary else None
        sentiment = analyze_sentiment(transcript_text) if generate_sentiment else None
        keywords = extract_keywords(transcript_text) if generate_keywords else None

        return TranscriptionOut(
            transcript=transcript_text,
            summary=summary,
            sentiment=sentiment,
            keywords=keywords,
            subtitles=None,
        )
    finally:
        # Clean up temp files
        for path in (input_path, audio_path):  # type: ignore[name-defined]
            try:
                os.remove(path)
            except FileNotFoundError:
                # already deleted
                pass
            except Exception as e:
                logger.warning(f"Could not remove temp file {path}: {e}")
