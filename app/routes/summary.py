# ---- EchoScript.AI: routes/summary.py ----

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.utils.gpt_logic import summarize_transcript
from app.utils.redis_client import redis_client
from app.utils.logger import logger

router = APIRouter(prefix="/summary", tags=["Summarization"])

class SummaryRequest(BaseModel):
    transcript: str = Field(..., description="Full transcript to summarize")
    tone: Literal["default", "friendly", "formal", "bullet", "action"] = "default"
    length: Literal["short", "medium", "long"] = "medium"

class SummaryResponse(BaseModel):
    summary: str
    cached: bool
    tone: str
    length: str

@router.post("/", response_model=SummaryResponse)
async def summarize(req: SummaryRequest):
    transcript = req.transcript.strip()

    if not transcript:
        logger.warning("⚠️ Summary request failed: Empty transcript")
        raise HTTPException(status_code=400, detail="Transcript is empty.")

    if len(transcript.split()) < 10:
        logger.warning("⚠️ Transcript too short to summarize meaningfully.")
        raise HTTPException(status_code=400, detail="Transcript too short to summarize.")

    # Build Redis cache key
    cache_key = f"summary:{hash(transcript)}:{req.tone}:{req.length}"
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"📦 Returning cached summary for tone='{req.tone}', length='{req.length}'")
        return SummaryResponse(summary=cached, cached=True, tone=req.tone, length=req.length)

    try:
        # Generate new summary using GPT
        summary = summarize_transcript(
            text=transcript,
            tone=req.tone,
            length=req.length
        )
        # Cache result for 1 hour
        redis_client.set(cache_key, summary, ex=3600)

        logger.info(f"✅ Summary generated [tone: {req.tone}, length: {req.length}]")
        return SummaryResponse(summary=summary, cached=False, tone=req.tone, length=req.length)

    except Exception as e:
        logger.error(f"❌ Error during summary generation: {e}")
        raise HTTPException(status_code=500, detail="Summary generation failed. Please try again later.")
