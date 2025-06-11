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

# === Schema Definitions ===
class TranslateRequest(BaseModel):
    text: str = Field(..., description="Transcript or text to translate")
    target_lang: str = Field(..., description="Target language (e.g. 'en', 'es', 'fr')")
    tone: Literal["neutral", "formal", "friendly", "professional"] = "neutral"

class TranslateResponse(BaseModel):
    translated: str
    lang: str
    tone: str
    cached: bool

# === Translation Route ===
@router.post("/", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    cleaned_text = req.text.strip()
    if not cleaned_text:
        logger.warning("[Translate] ❌ Empty input")
        raise HTTPException(status_code=400, detail="Translation input is empty.")

    # Generate consistent cache key
    digest = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    cache_key = f"translate:{digest}:{req.target_lang}:{req.tone}"

    # Check Redis cache
    cached = redis_client.get(cache_key)
    if cached:
        try:
            decompressed = zlib.decompress(cached).decode("utf-8")
            logger.info(f"[Translate] 🧠 Returned from cache — {req.target_lang} ({req.tone})")
            return TranslateResponse(
                translated=decompressed,
                lang=req.target_lang,
                tone=req.tone,
                cached=True
            )
        except Exception as e:
            logger.warning(f"[Translate] ⚠️ Failed to decompress cache: {e}")

    # If not cached, call GPT translation
    try:
        translated = await translate_text(text=cleaned_text, target_language=req.target_lang, tone=req.tone)
        redis_client.setex(cache_key, 3600, zlib.compress(translated.encode("utf-8")))

        logger.info(f"[Translate] ✅ GPT translation complete → {req.target_lang} [{req.tone}]")
        return TranslateResponse(
            translated=translated,
            lang=req.target_lang,
            tone=req.tone,
            cached=False
        )
    except Exception as e:
        logger.error(f"[Translate] ❌ GPT translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation failed. Please try again later.")
