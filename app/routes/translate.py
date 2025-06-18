# ---- EchoScript.AI: routes/translate.py ----

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.utils.gpt_logic import translate_text
from app.utils.redis_client import redis_client
from app.utils.logger import logger
import hashlib
import zlib

router = APIRouter(prefix="/translate", tags=["Translation"])

# === Request Schema ===
class TranslateRequest(BaseModel):
    text: str = Field(..., description="Transcript or text to translate")
    target_lang: str = Field(..., min_length=2, max_length=5, description="Target language code (e.g. 'en', 'es', 'fr')")
    tone: Literal["neutral", "formal", "friendly", "professional"] = "neutral"

# === Response Schema ===
class TranslateResponse(BaseModel):
    translated: str
    lang: str
    tone: str
    cached: bool

# === Translation Endpoint ===
@router.post("/", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    # === Sanitize input ===
    cleaned_text = req.text.strip()
    if not cleaned_text:
        logger.warning("[Translate] ❌ Empty input provided.")
        raise HTTPException(status_code=400, detail="Translation input cannot be empty.")

    if len(cleaned_text) > 5000:
        logger.warning("[Translate] ⚠️ Input too long.")
        raise HTTPException(status_code=413, detail="Input text too long. Please limit to 5000 characters.")

    # === Create content hash for cache key ===
    digest = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    cache_key = f"translate:{digest}:{req.target_lang}:{req.tone}"

    # === Check Redis Cache ===
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                decompressed = zlib.decompress(cached).decode("utf-8")
                logger.info(f"[Translate] 🧠 Cache hit — {req.target_lang} ({req.tone})")
                return TranslateResponse(
                    translated=decompressed,
                    lang=req.target_lang,
                    tone=req.tone,
                    cached=True
                )
            except Exception as e:
                logger.warning(f"[Translate] ⚠️ Cache decompression failed: {e}")

    # === Call GPT Translation ===
    try:
        translated = await translate_text(
            text=cleaned_text,
            target_language=req.target_lang,
            tone=req.tone
        )

        if redis_client:
            try:
                redis_client.setex(cache_key, 3600, zlib.compress(translated.encode("utf-8")))
            except Exception as e:
                logger.warning(f"[Translate] ⚠️ Failed to cache translation: {e}")

        logger.info(f"[Translate] ✅ Translation complete → {req.target_lang} [{req.tone}]")
        return TranslateResponse(
            translated=translated,
            lang=req.target_lang,
            tone=req.tone,
            cached=False
        )

    except HTTPException:
        raise  # Don't rewrap known FastAPI exceptions
    except Exception as e:
        logger.exception(f"[Translate] ❌ GPT translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation failed. Please try again later.")

