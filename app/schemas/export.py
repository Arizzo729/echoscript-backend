# app/schemas/export.py

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ExportRequest(BaseModel):
    """
    Request schema for exporting a transcript in a given format.
    """

    transcript_id: int = Field(
        ..., description="Internal ID of the transcript to export"
    )
    format: Literal["txt", "pdf", "docx", "json"] = Field(
        ...,
        description="Desired export file format (e.g., 'txt', 'pdf', 'docx', 'json')",
    )


class ExportOut(BaseModel):
    """
    Response schema for export endpoint, returning a download URL.
    """

    url: HttpUrl = Field(
        ..., description="URL where the exported file can be downloaded"
    )
    filename: str = Field(
        ..., description="Suggested filename for the downloaded export"
    )

    class Config:
        schema_extra = {
            "example": {
                "url": "https://cdn.echoscript.ai/exports/transcript_1234.pdf",
                "filename": "transcript_1234.pdf",
            }
        }


__all__ = ["ExportRequest", "ExportOut"]
