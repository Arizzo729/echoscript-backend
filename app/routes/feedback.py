# ---- EchoScript.AI: routes/feedback.py ----

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from collections import Counter
from typing import Literal, List
from uuid import UUID, uuid4
from app.utils.logger import logger

router = APIRouter(prefix="/feedback", tags=["Feedback"])

# ---- Feedback Schema ----
class FeedbackEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    transcript_id: str = Field(..., description="ID of the transcript being reviewed")
    rating: int = Field(..., ge=1, le=5, description="User rating (1–5 stars)")
    comment: str = Field(default="", max_length=2000)
    emotion: Literal["positive", "neutral", "negative"] = "neutral"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ---- In-memory store (temporary) ----
feedback_db: List[FeedbackEntry] = []

# ---- Submit Feedback ----
@router.post("/", response_model=dict)
async def submit_feedback(entry: FeedbackEntry):
    feedback_db.append(entry)
    logger.info(f"📝 Feedback received for {entry.transcript_id} — Rating: {entry.rating}, Emotion: {entry.emotion}")
    return {
        "message": "Thanks! Your feedback was recorded.",
        "feedback_id": str(entry.id),
        "submitted_at": entry.timestamp.isoformat()
    }

# ---- Analytics Summary ----
@router.get("/analytics", response_model=dict)
async def get_feedback_summary():
    if not feedback_db:
        return {"total": 0, "ratings": {}, "emotions": {}}

    ratings = [fb.rating for fb in feedback_db]
    emotions = [fb.emotion for fb in feedback_db]

    return {
        "total": len(feedback_db),
        "ratings": dict(Counter(ratings)),
        "emotions": dict(Counter(emotions))
    }

# ---- Admin Access: List All Feedback (Optional) ----
@router.get("/all", response_model=List[FeedbackEntry])
async def list_all_feedback():
    return feedback_db

