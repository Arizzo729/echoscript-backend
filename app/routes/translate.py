# ---- EchoScript.AI: routes/translate.py ----

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.utils.gpt_logic import translate_text
from app.utils.redis_client import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/translate", tags=["Translation"])

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Transcript or text to translate")
    target_lang: str = Field(..., description="Target language (e.g. 'en', 'es', 'fr')")
    tone: Literal["neutral", "formal", "friendly", "professional"] = "neutral"

class TranslateResponse(BaseModel):
    translated: str
    lang: str
    tone: str
    cached: bool

@router.post("/", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Translation input is empty.")

    cache_key = f"translate:{hash(req.text)}:{req.target_lang}:{req.tone}"
    cached = redis_client.get(cache_key)
    if cached:
        return TranslateResponse(
            translated=cached,
            lang=req.target_lang,
            tone=req.tone,
            cached=True
        )

    try:
        translated = await translate_text(text=req.text, target_language=req.target_lang)
        redis_client.set(cache_key, translated, ex=3600)
        logger.info(f"✅ Translation complete to {req.target_lang} [{req.tone}]")
        return TranslateResponse(
            translated=translated,
            lang=req.target_lang,
            tone=req.tone,
            cached=False
        )
    except Exception as e:
        logger.error(f"❌ Translation failed: {e}")
        raise HTTPException(status_code=500, detail="Translation failed. Please try again later.")

