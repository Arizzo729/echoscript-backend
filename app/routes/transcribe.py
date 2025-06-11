# ---- EchoScript.AI Backend: routes/transcribe.py ----

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from uuid import uuid4
from datetime import datetime
import tempfile, os, logging, torch, openai, librosa, soundfile as sf, noisereduce as nr

from app.ai.servicesAutomationService import transcribeFile

router = APIRouter(prefix="/transcribe", tags=["Transcription"])

# ---- Device & API Setup ----
device = "cuda" if torch.cuda.is_available() else "cpu"
hf_token = os.getenv("HF_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

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
        # -- Step 1: Save temp file & reduce noise --
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        y, sr = librosa.load(tmp_path, sr=None)
        reduced_noise = nr.reduce_noise(y=y, sr=sr)
        sf.write(tmp_path, reduced_noise, 16000)

        # -- Step 2: Transcribe with Whisper CLI via automation service --
        transcript = await transcribeFile(tmp_path, langCode=language, model=model_size)

        # -- Step 3: AI Enhancement via GPT --
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
            "segments": [],  # Optional: replace if JSON output added
            "language": language,
            "timestamp": datetime.utcnow().isoformat()
        }

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
