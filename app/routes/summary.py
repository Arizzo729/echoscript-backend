# app/routes/summary.py — EchoScript.AI Smart Transcript Summarization with Plan Enforcement

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Literal
from app.utils.gpt_logic import summarize_transcript
from app.utils.redis_client import redis_client
from app.utils.logger import logger
import hashlib, zlib

from app.dependencies.plan_check import ensure_feature

router = APIRouter(prefix="/summary", tags=["Summarization"])

# === Request Schema ===
class SummaryRequest(BaseModel):
    transcript: str = Field(..., min_length=10, description="Transcript to summarize")
    tone: Literal["default", "friendly", "formal", "bullet", "action"] = "default"
    length: Literal["short", "medium", "long"] = "medium"

# === Response Schema ===
class SummaryResponse(BaseModel):
    summary: str
    cached: bool
    tone: str
    length: str

# === Summarization Endpoint ===
@router.post(
    "/",
    response_model=SummaryResponse,
    dependencies=[Depends(ensure_feature("summary"))]
)
async def summarize(req: SummaryRequest):
    """
    Summarize a transcript using GPT, with Redis caching and plan-based access control.
    """
    transcript = req.transcript.strip()

    # Validate input length
    word_count = len(transcript.split())
    if word_count < 10:
        logger.warning("[Summary] ❌ Too short to summarize.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript too short to summarize."
        )
    if word_count > 10000:
        logger.warning("[Summary] ⚠️ Input too large.")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Transcript too long to summarize."
        )

    # Build cache key
    digest = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    cache_key = f"summary:{digest}:{req.tone}:{req.length}"

    try:
        # === Check cache ===
        cached = redis_client.get(cache_key)
        if cached:
            summary = zlib.decompress(cached).decode("utf-8")
            logger.info(f"[Summary] ✅ Cache hit — tone={req.tone}, length={req.length}")
            return SummaryResponse(
                summary=summary,
                cached=True,
                tone=req.tone,
                length=req.length
            )

        # === Generate summary ===
        summary = await summarize_transcript(
            text=transcript,
            tone=req.tone,
            length=req.length
        )

        # === Cache result ===
        redis_client.setex(cache_key, 3600, zlib.compress(summary.encode("utf-8")))
        logger.info(f"[Summary] 🧠 GPT summary generated — tone={req.tone}, length={req.length}")

        return SummaryResponse(
            summary=summary,
            cached=False,
            tone=req.tone,
            length=req.length
        )

    except HTTPException:
        # Propagate client errors unchanged
        raise
    except Exception as e:
        logger.error(f"[Summary Error] ❌ GPT failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summary generation failed. Please try again later."
        )

