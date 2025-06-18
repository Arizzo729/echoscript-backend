# routes/summary.py — EchoScript.AI Smart Transcript Summarization

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.utils.gpt_logic import summarize_transcript
from app.utils.redis_client import redis_client
from app.utils.logger import logger
import hashlib, zlib

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
@router.post("/", response_model=SummaryResponse)
async def summarize(req: SummaryRequest):
    transcript = req.transcript.strip()

    if not transcript:
        logger.warning("[Summary] ❌ Empty input rejected.")
        raise HTTPException(status_code=400, detail="Transcript is empty.")

    if len(transcript.split()) < 10:
        logger.warning("[Summary] ❌ Too short to summarize.")
        raise HTTPException(status_code=400, detail="Transcript too short to summarize.")

    if len(transcript.split()) > 10000:
        logger.warning("[Summary] ⚠️ Input too large.")
        raise HTTPException(status_code=413, detail="Transcript too long to summarize.")

    digest = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    cache_key = f"summary:{digest}:{req.tone}:{req.length}"

    try:
        # === Check cache ===
        cached = redis_client.get(cache_key)
        if cached:
            summary = zlib.decompress(cached).decode("utf-8")
            logger.info(f"[Summary] ✅ Returned cached — tone={req.tone}, length={req.length}")
            return SummaryResponse(summary=summary, cached=True, tone=req.tone, length=req.length)

        # === Generate summary ===
        summary = await summarize_transcript(
            text=transcript,
            tone=req.tone,
            length=req.length
        )

        # === Cache result ===
        redis_client.setex(cache_key, 3600, zlib.compress(summary.encode("utf-8")))
        logger.info(f"[Summary] 🧠 GPT summary generated — tone={req.tone}, length={req.length}")

        return SummaryResponse(summary=summary, cached=False, tone=req.tone, length=req.length)

    except Exception as e:
        logger.error(f"[Summary Error] ❌ GPT failed: {e}")
        raise HTTPException(status_code=500, detail="Summary generation failed. Please try again later.")
