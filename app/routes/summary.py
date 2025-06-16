# routes/summary.py — EchoScript.AI Smart Transcript Summarization

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.utils.gpt_logic import summarize_transcript
from app.utils.redis_client import redis_client
from app.utils.logger import logger
import hashlib
import zlib

router = APIRouter(prefix="/summary", tags=["Summarization"])

# === Request Schema ===
class SummaryRequest(BaseModel):
    transcript: str = Field(..., description="Full transcript to summarize")
    tone: Literal["default", "friendly", "formal", "bullet", "action"] = "default"
    length: Literal["short", "medium", "long"] = "medium"

# === Response Schema ===
class SummaryResponse(BaseModel):
    summary: str
    cached: bool
    tone: str
    length: str

# === Route Logic ===
@router.post("/", response_model=SummaryResponse)
async def summarize(req: SummaryRequest):
    transcript = req.transcript.strip()

    if not transcript:
        logger.warning("[Summary] Empty transcript rejected.")
        raise HTTPException(status_code=400, detail="Transcript is empty.")

    if len(transcript.split()) < 10:
        logger.warning("[Summary] Transcript too short to summarize meaningfully.")
        raise HTTPException(status_code=400, detail="Transcript too short to summarize.")

    # Generate a consistent secure hash key
    digest = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    cache_key = f"summary:{digest}:{req.tone}:{req.length}"

    try:
        # Check Redis cache
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"[Summary] ✅ Served from cache — tone='{req.tone}', length='{req.length}'")
            summary = zlib.decompress(cached).decode("utf-8")
            return SummaryResponse(summary=summary, cached=True, tone=req.tone, length=req.length)

        # Generate new summary
        summary = summarize_transcript(
            text=transcript,
            tone=req.tone,
            length=req.length
        )

        # Compress + cache for 1 hour
        redis_client.setex(cache_key, 3600, zlib.compress(summary.encode("utf-8")))
        logger.info(f"[Summary] ✨ Generated summary — tone='{req.tone}', length='{req.length}'")

        return SummaryResponse(summary=summary, cached=False, tone=req.tone, length=req.length)

    except Exception as e:
        logger.error(f"[Summary Error] Failed: {e}")
        raise HTTPException(status_code=500, detail="Summary generation failed.")
