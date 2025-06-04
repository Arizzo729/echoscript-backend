# ---- EchoScript.AI Backend: transcribe.py ----

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import tempfile, os
from datetime import datetime
from uuid import uuid4
import torch
import openai
import whisperx
import librosa
import soundfile as sf
import noisereduce as nr
import logging

router = APIRouter()

# ---- Environment & Device Setup ----
device = "cuda" if torch.cuda.is_available() else "cpu"
hf_token = os.getenv("HF_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---- Model Caching ----
model_cache = {}
align_cache = {}

# ---- Helpers ----

def safe_compute_type():
    try:
        if torch.cuda.is_available():
            major, _ = torch.cuda.get_device_capability(0)
            return "float16" if major >= 7 else "float32"
    except Exception as e:
        logging.warning(f"Compute type fallback due to error: {e}")
    return "float32"

def get_models(model_size: str, lang: str):
    if model_size not in model_cache:
        model_cache[model_size], metadata = whisperx.load_model(model_size, device, compute_type=safe_compute_type())
        align_cache[model_size] = whisperx.load_align_model(language_code=lang, device=device)
    return model_cache[model_size], align_cache[model_size]

# ---- Main Endpoint ----

@router.post("/transcribe-enhanced")
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
        # Step 1: Save + Denoise
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        y, sr = librosa.load(tmp_path, sr=None)
        reduced_noise = nr.reduce_noise(y=y, sr=sr)
        sf.write(tmp_path, reduced_noise, 16000)

        # Step 2: Transcription
        model, metadata = whisperx.load_model(model_size, device, compute_type=safe_compute_type())
        result = model.transcribe(tmp_path, language=None if language == "auto" else language)
        segments = result["segments"]
        transcript = result["text"]
        lang = result.get("language", language)

        # Step 3: Speaker Diarization
        diarizer = whisperx.DiarizationPipeline(use_auth_token=hf_token)
        diarized = diarizer(tmp_path)

        # Step 4: Word-Level Alignment
        align_model = whisperx.load_align_model(language_code=lang, device=device)
        aligned = whisperx.align(segments, align_model, metadata, tmp_path, device)
        speaker_words = whisperx.assign_word_speakers(aligned["word_segments"], diarized)

        # Step 5: Format with Speakers
        lines = []
        last_speaker = None
        for word in speaker_words:
            spk = word.get("speaker", "Speaker")
            if spk != last_speaker:
                lines.append(f"\n[{spk}]: ")
                last_speaker = spk
            lines.append(word["text"])
        diarized_text = "".join(lines).strip()

        # Step 6: GPT Enhancement
        final_output = await apply_gpt_cleanup(
            text=diarized_text,
            summarize=summarize,
            fillers=remove_fillers,
            label=label_speakers,
            enhance=enhance_readability
        )

        return {
            "filename": filename,
            "transcript": final_output,
            "original": transcript,
            "segments": segments,
            "language": lang,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.exception("Transcription failed.")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# ---- GPT Cleanup Utility ----

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
        logging.warning(f"GPT enhancement failed: {e}")
        return text

