# app/routes/transcribe.py
# === EchoScript.AI — Enhanced Transcription with Plan Enforcement + High-Performance Preprocessing ===

import os
import tempfile
import logging
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional

import torch
import librosa
import soundfile as sf
import noisereduce as nr
from fastapi import (
    APIRouter, File, UploadFile, Form,
    HTTPException, Depends, status
)
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.faster_whisper_service import transcribe_with_faster_whisper, load_whisper_model
from app.services.gpt_enhancer import enhance_transcript_gpt, translate_text
from app.auth.auth_utils import get_current_user_optional, get_current_user
from app.models.user import User
from app.models.usage_log import UsageLog
from app.db import get_db
from app.dependencies.check_minutes import check_minutes
from app.dependencies.plan_check import ensure_feature
from app.config.plans import PLAN_CONFIG

router = APIRouter(prefix="/transcribe", tags=["Transcription"])
logger = logging.getLogger("echoscript")

# Preload Whisper model once for high throughput
WHISPER_MODEL = load_whisper_model()

class Segment(BaseModel):
    start: float
    end: float
    text: str
    speaker: Optional[str]

class TranscriptionResponse(BaseModel):
    filename: str
    original: str
    transcript: str
    translated: Optional[str]
    segments: List[Segment]
    language: str
    speakers: List[str]
    used_minutes: float = Field(..., description="Minutes consumed by this transcription")
    remaining_minutes: float = Field(..., description="Remaining minutes in current 30-day window")
    timestamp: datetime


def precise_duration_minutes(path: str) -> float:
    """
    Quickly compute audio duration in minutes without full load.
    """
    try:
        duration_sec = librosa.get_duration(filename=path)
        return round(duration_sec / 60.0, 2)
    except Exception:
        logger.exception("[Audio] Duration calculation failed")
        return 0.0


def high_performance_preprocess(path: str) -> None:
    """
    Apply noise reduction and silence trimming to the audio file in-place.
    Offloads CPU-bound work to threadpool.
    """
    # Load and denoise
    y, sr = librosa.load(path, sr=None)
    reduced = nr.reduce_noise(y=y, sr=sr, prop_decrease=1.0)
    # Trim silence
    y_trimmed, _ = librosa.effects.trim(reduced, top_db=30)
    # Overwrite file
    sf.write(path, y_trimmed, sr)


@router.post(
    "/enhanced",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK
)
async def transcribe_enhanced(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model_size: str = Form("medium"),
    summarize: bool = Form(False),
    remove_fillers: bool = Form(False),
    label_speakers: bool = Form(True),
    enhance_readability: bool = Form(True),
    translation_lang: Optional[str] = Form(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> TranscriptionResponse:
    """
    High-performance transcription pipeline:
    1. In-memory noise reduction & silence trim in threadpool
    2. Whisper transcription with beam search & temperature ensemble
    3. GPT-based enhancement & optional translation
    4. Plan feature & rolling-window quota enforcement
    """
    tmp_path = None
    filename = f"transcript_{uuid4().hex}_{file.filename}"
    try:
        # STEP 1: Save upload to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # STEP 2: Preprocess (noise reduction + trim) off main thread
        await run_in_threadpool(high_performance_preprocess, tmp_path)
        logger.info("[Audio] ✅ Preprocessing complete (noise reduction + trimming)")

        # STEP 3: Compute duration
        duration = precise_duration_minutes(tmp_path)
        if duration < 0.1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio too short or unreadable."
            )

        # STEP 4: Plan enforcement
        if user:
            ensure_feature("transcribe")()
            # Rolling window minute check
            check_minutes(duration)(user=user, db=db)
        else:
            # Guest enforcement
            limit = PLAN_CONFIG["guest"]["minutes_limit"]
            used = getattr(transcribe_enhanced, "guest_usage", 0.0)
            if used + duration > limit:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=(f"Guest limit exceeded: {used:.2f}/{limit} minutes used.")
                )
            transcribe_enhanced.guest_usage = used + duration

        # STEP 5: Transcribe with Whisper (GPU accelerated)
        result = await WHISPER_MODEL.transcribe_async(
            tmp_path,
            language=language,
            beam_size=5,
            best_of=3,
            word_timestamps=True,
            diarization=label_speakers,
            temperature=[0.0]
        )
        raw_text = result.text
        segments_data = [
            Segment(
                start=s.start,
                end=s.end,
                text=s.text,
                speaker=getattr(s, "speaker", None)
            ) for s in result.segments
        ]
        detected_lang = result.language or language
        speakers = list({seg.speaker for seg in result.segments if hasattr(seg, "speaker")})

        # STEP 6: GPT enhancement off main thread
        enhanced_text = await run_in_threadpool(
            enhance_transcript_gpt,
            raw_text,
            summarize,
            remove_fillers,
            label_speakers,
            enhance_readability
        )

        # STEP 7: Optional translation
        translated_text: Optional[str] = None
        if translation_lang and translation_lang != detected_lang:
            try:
                translated_text = await run_in_threadpool(
                    translate_text,
                    enhanced_text,
                    translation_lang
                )
            except Exception:
                logger.warning("[Translation] ⚠️ Skipped due to error")

        # STEP 8: Compute remaining minutes
        if user:
            threshold = datetime.utcnow() - timedelta(days=30)
            used_30 = db.query(func.coalesce(func.sum(UsageLog.transcript_minutes), 0.0))\
                         .filter(UsageLog.user_id == user.id, UsageLog.created_at >= threshold)\
                         .scalar() or 0.0
            remaining = round(max(0.0, PLAN_CONFIG[user.plan]["minutes_limit"] - used_30), 2)
        else:
            remaining = round(max(0.0, PLAN_CONFIG["guest"]["minutes_limit"] - transcribe_enhanced.guest_usage), 2)

        return TranscriptionResponse(
            filename=filename,
            original=raw_text,
            transcript=enhanced_text,
            translated=translated_text,
            segments=segments_data,
            language=detected_lang,
            speakers=speakers,
            used_minutes=round(duration, 2),
            remaining_minutes=remaining,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[Transcribe] ❌ Unexpected error in transcription pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription service error."
        )
    finally:
        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

