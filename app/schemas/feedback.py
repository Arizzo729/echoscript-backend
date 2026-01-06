from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    transcript_id: int = Field(
        ..., description="ID of the transcript being reviewed", example=101
    )
    rating: int = Field(..., description="Rating given by the user (1-5)", example=4)
    comment: str | None = Field(
        None,
        description="Optional feedback comment",
        example="Very accurate transcript.",
    )
    emotion: str | None = Field(
        None, description="Detected or expressed emotion", example="satisfied"
    )


class FeedbackResponse(BaseModel):
    feedback_id: int = Field(
        ..., description="Unique ID for this feedback entry", example=456
    )
    message: str = Field(
        ...,
        description="Feedback acknowledgment message",
        example="Feedback submitted successfully.",
    )
    status: str = Field(
        ..., description="Status of the feedback submission", example="received"
    )
    submitted_at: datetime = Field(
        ..., description="UTC timestamp of submission", example="2025-07-23T15:00:00"
    )


__all__ = ["FeedbackRequest", "FeedbackResponse"]
