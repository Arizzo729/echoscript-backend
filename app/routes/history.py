# app/routes/assistant.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.utils.logger import logger

router = APIRouter()

# In-memory feedback store (placeholder for future persistence)
_feedback_store: list[dict] = []

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the AI Assistant a question based on a transcript",
)
async def ask_assistant(
    ask_req: AskRequest,
    db: Session = Depends(get_db),  # kept for future logging
    current_user=Depends(get_current_user),
) -> AskResponse:
    """
    Placeholder response for assistant query until LLM integration is implemented.
    """
    # You can later replace this with your actual LLM integration (e.g., local model)
    dummy_answer = f"(Mock response) You asked: '{ask_req.question}' about transcript of length {len(ask_req.transcript)}"
    return AskResponse(answer=dummy_answer, tokens_used=0)


@router.post(
    "/train",
    response_model=TrainResponse,
    summary="Submit feedback for assistant responses",
)
async def train_assistant(
    train_req: TrainRequest,
    current_user=Depends(get_current_user),
) -> TrainResponse:
    """
    Collect feedback on assistant answers for future model training.
    """
    _feedback_store.append(
        {
            "user_id": current_user.id,
            "transcript": train_req.transcript,
            "question": train_req.question,
            "answer": train_req.answer,
            "rating": train_req.rating,
            "feedback": train_req.feedback,
        }
    )
    logger.info(f"Received assistant feedback from user {current_user.id}")
    return TrainResponse(status="received")


__all__ = ["ask_assistant", "train_assistant"]

