from typing import Optional

from pydantic import BaseModel, Field


class SubtitleOut(BaseModel):
    """
    Response schema for subtitle generation results.
    """

    subtitles: str = Field(
        ...,
        description="Subtitle text including timestamps, suitable for display or download",
    )
    language: Optional[str] = Field(
        None,
        description="ISO language code of the subtitles (e.g., 'en', 'es'), if translated",
    )
    format: Optional[str] = Field(
        "srt",
        description="Subtitle format (e.g., 'srt' for SubRip, 'txt' for plain text)",
    )

    class Config:
        orm_mode = True


__all__ = [
    "SubtitleOut",
]
