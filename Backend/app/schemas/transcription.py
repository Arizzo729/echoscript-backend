from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptionOut(BaseModel):
    """
    Response schema for transcription results.
    """

    transcript: str = Field(..., description="Raw transcription text")
    summary: Optional[str] = Field(
        None, description="AI-generated summary of the transcription"
    )
    sentiment: Optional[str] = Field(
        None, description="Sentiment label of the transcription"
    )
    keywords: Optional[List[str]] = Field(
        None, description="Extracted keywords or key phrases"
    )
    subtitles: Optional[str] = Field(
        None, description="Subtitle text with timestamps (SRT or plain text)"
    )

    class Config:
        orm_mode = True


__all__ = [
    "TranscriptionOut",
]
