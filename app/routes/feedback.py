# routes/feedback.py — EchoScript.AI Feedback & Analytics

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, List
from uuid import UUID, uuid4
from collections import Counter
from app.utils.logger import logger

router = APIRouter(prefix="/feedback", tags=["Feedback"])

# === Schema ===
class FeedbackEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    transcript_id: str = Field(..., description="The transcript being rated")
    rating: int = Field(..., ge=1, le=5, description="Star rating (1–5)")
    comment: str = Field(default="", max_length=2000)
    emotion: Literal["positive", "neutral", "negative"] = "neutral"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# === In-Memory Store (temporary) ===
feedback_db: List[FeedbackEntry] = []

# === Submit Feedback ===
@router.post("/", response_model=dict)
async def submit_feedback(entry: FeedbackEntry):
    feedback_db.append(entry)
    logger.info(f"[Feedback] {entry.transcript_id} ⭐ {entry.rating} | {entry.emotion}")
    return {
        "message": "Thanks! Your feedback has been recorded.",
        "feedback_id": str(entry.id),
        "submitted_at": entry.timestamp.isoformat()
    }

# === Summary Analytics ===
@router.get("/analytics", response_model=dict)
async def get_feedback_summary():
    if not feedback_db:
        return {"total": 0, "ratings": {}, "emotions": {}}

    ratings = [entry.rating for entry in feedback_db]
    emotions = [entry.emotion for entry in feedback_db]

    summary = {
        "total": len(feedback_db),
        "ratings": dict(sorted(Counter(ratings).items())),
        "emotions": dict(sorted(Counter(emotions).items()))
    }

    return summary

# === Admin: List All Feedback ===
@router.get("/all", response_model=List[FeedbackEntry])
async def list_all_feedback():
    return sorted(feedback_db, key=lambda x: x.timestamp, reverse=True)
