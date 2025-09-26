from pydantic import BaseModel, Field


class TranscriptionOut(BaseModel):
    """
    Response schema for transcription results.
    """

    transcript: str = Field(..., description="Raw transcription text")
    summary: str | None = Field(
        None, description="AI-generated summary of the transcription"
    )
    sentiment: str | None = Field(
        None, description="Sentiment label of the transcription"
    )
    keywords: list[str] | None = Field(
        None, description="Extracted keywords or key phrases"
    )
    subtitles: str | None = Field(
        None, description="Subtitle text with timestamps (SRT or plain text)"
    )

    class Config:
        orm_mode = True


__all__ = [
    "TranscriptionOut",
]
