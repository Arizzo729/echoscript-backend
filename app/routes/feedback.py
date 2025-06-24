from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, List, Optional
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
    user_id: Optional[str] = Field(default=None, description="Optional user ID for analytics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# === In-Memory Store (Temporary) ===
feedback_db: List[FeedbackEntry] = []

# === Submit Feedback ===
@router.post("/", response_model=dict)
async def submit_feedback(entry: FeedbackEntry):
    feedback_db.append(entry)
    logger.info(f"[Feedback] Transcript {entry.transcript_id} | ⭐ {entry.rating} | {entry.emotion} | User: {entry.user_id or 'Anonymous'}")
    return {
        "message": "🎉 Feedback submitted successfully!",
        "feedback_id": str(entry.id),
        "submitted_at": entry.timestamp.isoformat()
    }

# === Summary Analytics ===
@router.get("/analytics", response_model=dict)
async def get_feedback_summary():
    if not feedback_db:
        return {
            "total": 0,
            "average_rating": 0.0,
            "ratings": {},
            "emotions": {}
        }

    ratings = [entry.rating for entry in feedback_db]
    emotions = [entry.emotion for entry in feedback_db]
    total = len(ratings)

    summary = {
        "total": total,
        "average_rating": round(sum(ratings) / total, 2),
        "ratings": dict(sorted(Counter(ratings).items())),
        "emotions": dict(sorted(Counter(emotions).items()))
    }

    return summary

# === Filtered Feedback View ===
@router.get("/filter", response_model=List[FeedbackEntry])
async def filter_feedback(
    transcript_id: Optional[str] = Query(None, description="Filter by transcript ID"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating to include"),
    emotion: Optional[str] = Query(None, description="Filter by emotion")
):
    filtered = feedback_db
    if transcript_id:
        filtered = [f for f in filtered if f.transcript_id == transcript_id]
    if min_rating:
        filtered = [f for f in filtered if f.rating >= min_rating]
    if emotion:
        filtered = [f for f in filtered if f.emotion == emotion]

    return sorted(filtered, key=lambda x: x.timestamp, reverse=True)

# === Admin: List All Feedback ===
@router.get("/all", response_model=List[FeedbackEntry])
async def list_all_feedback():
    return sorted(feedback_db, key=lambda x: x.timestamp, reverse=True)
