# app/routes/feedback.py
from fastapi import APIRouter, HTTPException, status

from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.utils.send_email import send_email

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("/", response_model=FeedbackResponse)
def send_feedback(request: FeedbackRequest) -> FeedbackResponse:
    try:
        send_email(
            to_address="feedback@echoscript.ai",
            subject=f"[Feedback] {request.topic or 'General'}",
            body=request.message,
        )
        return FeedbackResponse(ok=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed: {e}"
        )
