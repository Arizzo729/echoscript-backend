"""
app/schemas/assistant.py: Pydantic models for the AI assistant endpoints and alias definitions.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AssistantQuery(BaseModel):
    transcript: str = Field(
        ...,
        description="Full transcript context",
        examples=["Sample transcript text of a conversation."],
    )
    question: str = Field(
        ...,
        description="User's query or question",
        examples=["What is the main point of the conversation?"],
    )
    history: List[str] = Field(
        default_factory=list,
        description="Prior conversation history messages",
        examples=[["Previous user message", "Previous assistant reply"]],
    )
    user_id: str = Field(
        default="default",
        description="Identifier for the user (used for context memory)",
        examples=["user123"],
    )
    mode: Optional[str] = Field(
        default="auto",
        description="Mode of response (use 'auto' for automatic mode selection)",
        examples=["auto"],
    )
    tone: Optional[Literal["friendly", "formal", "neutral"]] = Field(
        default="friendly",
        description="Tone of the assistant's response",
        examples=["friendly"],
    )
    voice: Optional[Literal["expert", "teacher", "casual", "technical"]] = Field(
        default="expert",
        description="Voice style of the assistant's response",
        examples=["expert"],
    )


class AssistantResponse(BaseModel):
    response: str = Field(..., description="The assistant's answer or output text")
    mode: str = Field(
        ..., description="The mode that was determined or used for this response"
    )


class TrainingExample(BaseModel):
    user_id: str
    transcript: str
    question: str
    answer: str
    rating: Optional[int] = None
    feedback: Optional[str] = None


# --- Aliases so your routes can keep using the old names ---
AskRequest = AssistantQuery
AskResponse = AssistantResponse


class TrainRequest(BaseModel):
    transcript: str
    question: str
    answer: str
    rating: int
    feedback: Optional[str] = None


class TrainResponse(BaseModel):
    status: str


__all__ = [
    "AssistantQuery",
    "AssistantResponse",
    "TrainingExample",
    "AskRequest",
    "AskResponse",
    "TrainRequest",
    "TrainResponse",
]
