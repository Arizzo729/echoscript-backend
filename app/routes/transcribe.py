# === EchoScript.AI — routes/transcribe.py (Ultimate Enhanced Transcription) ===

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from uuid import uuid4
from datetime import datetime
from collections import defaultdict
import tempfile, os, logging, torch, librosa, soundfile as sf, noisereduce as nr

from app.services.faster_whisper_service import transcribe_with_faster_whisper
from app.services.gpt_enhancer import enhance_transcript_gpt
from app.auth.auth_utils import get_current_user_optional
from app.models import User

router = APIRouter(prefix="/transcribe", tags=["Transcription"])

# === Device Setup ===
device = "cuda" if torch.cuda.is_available() else "cpu"

# === Usage Tracking ===
GUEST_LIMIT_MINUTES = 60
usage_tracker = defaultdict(float)

def get_audio_duration_minutes(path):
    try:
        y, sr = librosa.load(path, sr=None)
        return round(librosa.get_duration(y=y, sr=sr) / 60, 2)
    except Exception as e:
        logging.exception("[Audio] Duration calculation failed")
        return 0.0

# === Endpoint ===
@router.post("/enhanced")
async def transcribe_enhanced(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model_size: str = Form("medium"),
    summarize: bool = Form(False),
    remove_fillers: bool = Form(False),
    label_speakers: bool = Form(True),
    enhance_readability: bool = Form(True),
    translation_lang: str = Form(None),
    user: User = Depends(get_current_user_optional)
):
    tmp_path = None
    filename = f"transcript_{uuid4().hex}_{file.filename}"
    client_id = user.id if user else "guest"

    try:
        # === Step 1: Save audio ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # === Step 2: Noise Reduction ===
        y, sr = librosa.load(tmp_path, sr=None)
        reduced = nr.reduce_noise(y=y, sr=sr, prop_decrease=1.0)
        sf.write(tmp_path, reduced, sr)
        logging.info("[Audio] ✅ Denoising complete")

        # === Step 3: Duration Check ===
        duration = get_audio_duration_minutes(tmp_path)
        if duration < 0.2:
            raise HTTPException(status_code=400, detail="Audio too short or unreadable.")

        # === Step 4: Guest Usage Check ===
        used = usage_tracker[client_id]
        remaining = GUEST_LIMIT_MINUTES - used
        if not user and used + duration > GUEST_LIMIT_MINUTES:
            raise HTTPException(
                status_code=403,
                detail=f"⛔ Guest limit exceeded: {used:.2f}/{GUEST_LIMIT_MINUTES} min used."
            )
        usage_tracker[client_id] += duration
        logging.info(f"[Usage] {client_id}: {duration:.2f} min (total: {usage_tracker[client_id]:.2f})")

        # === Step 5: Transcribe ===
        result = await transcribe_with_faster_whisper(
            path=tmp_path,
            lang=language,
            model_size=model_size,
            device=device,
            word_timestamps=True,
            diarization=label_speakers
        )

        raw_text = result["text"]
        segments = result.get("segments", [])
        detected_lang = result.get("language", language)
        speaker_labels = result.get("speakers")

        # === Step 6: Enhance ===
        enhanced_text = await enhance_transcript_gpt(
            text=raw_text,
            summarize=summarize,
            fillers=remove_fillers,
            label=label_speakers,
            enhance=enhance_readability
        )

        # === Step 7: Optional Translation ===
        translated_text = None
        if translation_lang and translation_lang != detected_lang:
            from app.services.gpt_enhancer import translate_text
            try:
                translated_text = await translate_text(
                    text=enhanced_text,
                    target_language=translation_lang
                )
            except Exception as e:
                logging.warning(f"[Translation] ⚠️ Failed: {e}")

        return {
            "filename": filename,
            "original": raw_text,
            "transcript": enhanced_text,
            "translated": translated_text,
            "segments": segments,
            "language": detected_lang,
            "speakers": speaker_labels,
            "used_minutes": round(usage_tracker[client_id], 2),
            "remaining_minutes": round(max(0, remaining - duration), 2),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("[Transcribe] ❌ Fatal error during transcription pipeline")
        raise HTTPException(status_code=500, detail="Internal server error during transcription.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

