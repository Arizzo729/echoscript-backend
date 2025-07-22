from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.utils.logger import logger

router = APIRouter()

# In-memory store for feedback submissions (replace with DB integration if needed)
_feedback_store = []


@router.post(
    "/", response_model=FeedbackResponse, summary="Submit feedback for a transcript"
)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FeedbackResponse:
    """
    Receive user feedback on a completed transcript.
    Stores rating, comment, and emotion for analysis.
    """
    try:
        # Store feedback in-memory for now
        _feedback_store.append(
            {
                "user_id": current_user.id,
                "transcript_id": request.transcript_id,
                "rating": request.rating,
                "comment": request.comment,
                "emotion": request.emotion,
            }
        )
        logger.info(
            f"Received feedback from user {current_user.id} on transcript {request.transcript_id}: "
            f"rating={request.rating}, emotion={request.emotion}, comment={request.comment}"
        )
        return FeedbackResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to submit feedback at this time",
        )
