from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from uuid import uuid4
from datetime import datetime
import tempfile, os, logging, torch, openai, librosa, soundfile as sf, noisereduce as nr
from collections import defaultdict

from app.ai.servicesAutomationService import transcribeFile

router = APIRouter(prefix="/transcribe", tags=["Transcription"])

# ---- Device & API Setup ----
device = "cuda" if torch.cuda.is_available() else "cpu"
hf_token = os.getenv("HF_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---- Transcription Limit Configuration ----
GUEST_LIMIT_MINUTES = 60
guest_usage_minutes = defaultdict(float)

def get_audio_duration_minutes(path):
    try:
        y, sr = librosa.load(path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        return round(duration / 60, 2)
    except Exception as e:
        logging.error(f"[Duration] Failed to calculate audio duration: {e}")
        return 0

# ---- Enhanced Transcription Endpoint ----
@router.post("/enhanced")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model_size: str = Form("base"),
    summarize: bool = Form(False),
    remove_fillers: bool = Form(False),
    label_speakers: bool = Form(True),
    enhance_readability: bool = Form(True)
):
    filename = f"transcript_{uuid4().hex}_{file.filename}"
    tmp_path = None

    try:
        # -- Step 1: Save temp file --
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # -- Step 2: Noise reduction --
        y, sr = librosa.load(tmp_path, sr=None)
        reduced_noise = nr.reduce_noise(y=y, sr=sr)
        sf.write(tmp_path, reduced_noise, 16000)
        logging.info("[Transcribe] Noise reduction complete.")

        # -- Step 3: Duration check --
        audio_minutes = get_audio_duration_minutes(tmp_path)
        client_id = "guest"  # replace later with IP/session/user ID

        used = guest_usage_minutes[client_id]
        remaining = max(0, GUEST_LIMIT_MINUTES - used)

        if used + audio_minutes > GUEST_LIMIT_MINUTES:
            raise HTTPException(
                status_code=403,
                detail=f"⛔ Monthly transcription limit exceeded. You've used {used:.2f} of {GUEST_LIMIT_MINUTES} minutes. Please upgrade or wait until next month."
            )

        guest_usage_minutes[client_id] += audio_minutes
        logging.info(f"[Limit] {client_id} used {audio_minutes:.2f} min (total: {guest_usage_minutes[client_id]:.2f})")

        # -- Step 4: Transcribe --
        transcript = await transcribeFile(tmp_path, langCode=language, model=model_size)
        logging.info("[Transcribe] Whisper transcription complete.")

        # -- Step 5: Enhance with GPT --
        final_output = await apply_gpt_cleanup(
            text=transcript,
            summarize=summarize,
            fillers=remove_fillers,
            label=label_speakers,
            enhance=enhance_readability
        )

        return {
            "filename": filename,
            "transcript": final_output,
            "original": transcript,
            "segments": [],  # add if needed later
            "language": language,
            "used_minutes": round(guest_usage_minutes[client_id], 2),
            "remaining_minutes": round(GUEST_LIMIT_MINUTES - guest_usage_minutes[client_id], 2),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException as he:
        raise he

    except Exception as e:
        logging.exception("[Transcribe] ❌ Failed to process file.")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# ---- GPT Enhancement Helper ----
async def apply_gpt_cleanup(text, summarize=False, fillers=False, label=False, enhance=True):
    prompt = f"Clean up this transcript:\n\n{text.strip()}\n\n"
    if fillers:
        prompt += "Remove filler words like 'um', 'uh', 'like', etc.\n"
    if enhance:
        prompt += "Fix grammar, sentence structure, and improve readability.\n"
    if label:
        prompt += "Preserve and clearly format speaker labels.\n"
    if summarize:
        prompt += "Add a concise bullet-point summary at the end.\n"

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert transcription editor and summarizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.warning(f"[GPT Cleanup] ⚠️ GPT failed: {e}")
        return text


