import whisperx
import torch
import os
from app.config import HF_TOKEN
from app.utils.logger import logger

# ---- Device Setup ----
device = "cuda" if torch.cuda.is_available() else "cpu"
model_cache = {}
align_cache = {}

# ---- Load Transcription Model ----
def load_whisperx_model(model_size: str = "medium", lang: str = "en"):
    if model_size not in model_cache:
        try:
            model = whisperx.load_model(model_size, device)
            model_cache[model_size] = model
            logger.info(f"✅ WhisperX model loaded: {model_size}")
        except Exception as e:
            logger.error(f"❌ Failed to load WhisperX model: {e}")
            raise
    return model_cache[model_size]

# ---- Load Alignment Model ----
def load_alignment_model(lang: str = "en"):
    if lang not in align_cache:
        try:
            align_model = whisperx.load_align_model(language_code=lang, device=device)
            align_cache[lang] = align_model
            logger.info(f"✅ Align model loaded for language: {lang}")
        except Exception as e:
            logger.error(f"❌ Failed to load alignment model: {e}")
            raise
    return align_cache[lang]

# ---- Transcribe + Align Pipeline ----
def transcribe_with_whisperx(file_path: str, model_size: str = "medium", lang: str = "en", include_segments: bool = True):
    try:
        audio = whisperx.load_audio(file_path)
        logger.info(f"🔊 Audio loaded: {file_path}")

        model = load_whisperx_model(model_size, lang)
        result = model.transcribe(audio, language=lang)
        logger.info("🧠 Transcription complete.")

        align_model = load_alignment_model(lang)
        metadata = {"language": lang}
        result_aligned = whisperx.align(result["segments"], align_model, audio, metadata, device)
        logger.info("🧩 Word alignment complete.")

        return {
            "text": result_aligned.get("text", result.get("text", "")),
            "segments": result_aligned.get("segments") if include_segments else [],
            "language": result.get("language", lang)
        }

    except Exception as e:
        logger.error(f"❌ Transcription pipeline failed: {e}")
        return {
            "error": "Transcription failed.",
            "detail": str(e)
        }
