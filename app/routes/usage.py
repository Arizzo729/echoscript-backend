from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings, Settings
import json
import uuid
from app.utils.redis_client import cache  # safe, lazy, memory-fallback cache facade

log = logging.getLogger(__name__)
router = APIRouter(prefix="/usage")


class UsageSummaryOut(BaseModel):
    cached: bool
    summary: Dict[str, Any]


class UserUsageItem(BaseModel):
    user_id: str
    minutes: float = 0
    items: int = 0


class UsersUsageOut(BaseModel):
    users: list[UserUsageItem]


class SubmitTranscriptIn(BaseModel):
    user_id: Optional[str] = None
    transcript: str
    meta: Optional[Dict[str, Any]] = None


class SubmitTranscriptOut(BaseModel):
    ok: bool
    id: str


class GenerateSummaryIn(BaseModel):
    transcript: str
    tone: str = "default"
    length: str = "short"


class GenerateSummaryOut(BaseModel):
    summary: str
    cached: bool = False


@router.get("/summary", response_model=UsageSummaryOut)
async def usage_summary(
    request: Request, settings: Settings = Depends(get_settings)
) -> UsageSummaryOut:
    """
    Return an aggregated usage summary.
    Replace the placeholder 'computed' block with real DB aggregation if available.
    """
    try:
        raw_summary = cache.get("usage:summary")
        if raw_summary:
            summary = json.loads(raw_summary)
            return UsageSummaryOut(cached=True, summary=summary)
        # Placeholder compute (replace with your real logic)
        computed = {"users": 0, "minutes": 0, "items": 0}
        cache.set("usage:summary", computed, ex=300)  # cache for 5 minutes
        return UsageSummaryOut(cached=False, summary=computed)
    except Exception:
        log.exception("Could not compute usage summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not compute usage summary",
        )


@router.get("/users", response_model=UsersUsageOut)
async def users_usage(
    settings: Settings = Depends(get_settings)
) -> UsersUsageOut:
    """
    Return per-user usage.
    Extend this with filters (date range, org, plan, etc.) as needed.
    """
    try:
        # Placeholder data; integrate with your DB if available
        data: list[UserUsageItem] = []
        return UsersUsageOut(users=data)
    except Exception:
        log.exception("Could not fetch user usage")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch user usage",
        )


@router.post("/submitTranscript", status_code=status.HTTP_201_CREATED, response_model=SubmitTranscriptOut)
async def submit_transcript(
    payload: SubmitTranscriptIn,
    request: Request,
    # request parameter is used for future extensibility
    settings: Settings = Depends(get_settings),
) -> SubmitTranscriptOut:
    """
    Accepts a transcript payload and persists/queues it.
    Currently stores to cache as a demo; replace with DB/S3/queue.
    """

    key = f"transcript:{uuid.uuid4().hex}"

    try:
        user = payload.user_id or "anon"
        item = {"user_id": user, "transcript": payload.transcript, "meta": payload.meta or {}}
        cache.set(key, json.dumps(item), ex=3600)  # 1h TTL
        return SubmitTranscriptOut(ok=True, id=key)
    except Exception:
        log.exception("Could not submit transcript")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit transcript",
        )
    raise HTTPException(status_code=400, detail="Invalid payload: transcript required")


def _generate_summary_with_openai(transcript: str, tone: str, length: str) -> str:
    """Generate summary using OpenAI API."""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "⚠️ OpenAI API key not configured. Please add OPENAI_API_KEY to your environment variables."
        
        client = OpenAI(api_key=api_key)
        
        # Build the prompt based on tone and length
        tone_map = {
            "default": "smart and concise",
            "friendly": "friendly and conversational",
            "formal": "formal and professional",
            "bullet": "bullet points format",
            "action": "action-oriented with clear next steps"
        }
        
        length_map = {
            "short": "2-3 sentences",
            "medium": "1-2 paragraphs",
            "long": "3-4 paragraphs with detailed analysis"
        }
        
        tone_desc = tone_map.get(tone, "smart and concise")
        length_desc = length_map.get(length, "2-3 sentences")
        
        prompt = f"""You are a professional summarization assistant. Summarize the following transcript in a {tone_desc} tone. 
The summary should be approximately {length_desc} long.

Transcript:
{transcript}

Summary:"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates clear, structured summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.exception(f"Failed to generate summary with OpenAI: {e}")
        raise


@router.post("/summary", response_model=GenerateSummaryOut)
async def generate_summary(
    payload: GenerateSummaryIn,
    settings: Settings = Depends(get_settings),
) -> GenerateSummaryOut:
    """
    Generate an AI-powered summary of a transcript.
    Uses OpenAI GPT to create summaries based on tone and length preferences.
    Results are cached for 1 hour.
    """
    if not payload.transcript or not payload.transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript cannot be empty"
        )
    
    # Create cache key based on transcript, tone, and length
    cache_key = f"summary:{hash(f'{payload.transcript}:{payload.tone}:{payload.length}')}"
    
    try:
        # Check cache first
        cached_summary = cache.get(cache_key)
        if cached_summary:
            summary_text = cached_summary.decode("utf-8") if isinstance(cached_summary, bytes) else str(cached_summary)
            log.info(f"Returning cached summary for key: {cache_key}")
            return GenerateSummaryOut(summary=summary_text, cached=True)
        
        # Generate new summary
        log.info(f"Generating new summary with tone={payload.tone}, length={payload.length}")
        summary_text = _generate_summary_with_openai(
            payload.transcript,
            payload.tone,
            payload.length
        )
        
        # Cache the result for 1 hour
        cache.set(cache_key, summary_text, ex=3600)
        
        return GenerateSummaryOut(summary=summary_text, cached=False)
        
    except Exception as e:
        log.exception("Failed to generate summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate summary: {str(e)}"
        )
