# app/routes/assistant.py

from typing import Any

import openai
from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.config import config
from app.db import get_db
from app.dependencies import get_current_user
from app.schemas.assistant import (AskRequest, AskResponse, TrainRequest,
                                   TrainResponse)
from app.utils.logger import logger

# Alias ChatCompletion so MyPy recognizes it
ChatCompletion: Any = openai.ChatCompletion  # type: ignore[attr-defined]

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
    Use OpenAI to answer a question about the provided transcript.
    """
    if not config.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key is not configured.",
        )

    openai.api_key = config.OPENAI_API_KEY
    system_prompt = (
        "You are a helpful assistant that answers questions about transcripts. "
        "Use the transcript context to provide accurate answers."
    )
    user_prompt = f"Transcript:\n{ask_req.transcript}\n\nQuestion: {ask_req.question}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
        )
        # Extract answer and token usage
        answer = response.choices[0].message.content.strip()
        usage = getattr(response, "usage", None)
        total_tokens = getattr(usage, "total_tokens", None) if usage else None
        return AskResponse(answer=answer, tokens_used=total_tokens)

    except OpenAIError as e:
        logger.error(f"OpenAI API error in /assistant/ask: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error communicating with OpenAI service.",
        )


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
