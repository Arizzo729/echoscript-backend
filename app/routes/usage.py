from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings, Settings
from app.utils.redis_client import cache  # safe, lazy, memory-fallback cache facade

log = logging.getLogger(__name__)
router = APIRouter()


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


@router.get("/usage/summary", response_model=UsageSummaryOut)
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


@router.get("/users/usage", response_model=UsersUsageOut)
async def users_usage(
    request: Request, settings: Settings = Depends(get_settings)
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
    settings: Settings = Depends(get_settings),
) -> SubmitTranscriptOut:
    """
    Accepts a transcript payload and persists/queues it.
    Currently stores to cache as a demo; replace with DB/S3/queue.
    """
    if not payload.transcript or not isinstance(payload.transcript, str):
        raise HTTPException(status_code=400, detail="Invalid payload: transcript required")

    try:
        user = payload.user_id or "anon"
        key = f"transcript:latest:{user}"
        item = {"user_id": user, "transcript": payload.transcript, "meta": payload.meta or {}}
        cache.set(key, json.dumps(item), ex=3600)  # 1h TTL
        return SubmitTranscriptOut(ok=True, id=key)
    except Exception:
        log.exception("Could not submit transcript")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit transcript",
        )
