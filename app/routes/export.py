# routes/export.py — EchoScript.AI Transcript Export System

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Literal
import os
import mimetypes

from app.utils.export_utils import generate_export_file
from app.utils.logger import logger

router = APIRouter(prefix="/export", tags=["Export"])

# --- Supported Formats ---
VALID_FORMATS = ["txt", "docx", "pdf", "json"]

# --- Response Schema (not used directly, but good for OpenAPI) ---
class ExportResponse(BaseModel):
    filename: str
    download_url: str
    format: Literal["txt", "docx", "pdf", "json"]

# --- Export Endpoint ---
@router.get("/", response_model=None, responses={200: {"content": {"application/octet-stream": {}}}})
def export_transcript(
    transcript_id: str = Query(..., description="The unique ID of the transcript to export."),
    format: Literal["txt", "docx", "pdf", "json"] = Query("txt", description="Export file format.")
):
    """
    Export a transcript to a downloadable file (TXT, DOCX, PDF, or JSON).
    """
    try:
        export_path = generate_export_file(transcript_id, format)

        if not os.path.isfile(export_path):
            logger.error(f"[Export] File missing: {export_path}")
            raise HTTPException(status_code=404, detail="Export file not found.")

        filename = f"transcript_{transcript_id}.{format}"
        media_type = mimetypes.guess_type(export_path)[0] or "application/octet-stream"

        logger.info(f"[Export] Download ready: {filename} ({media_type})")

        return FileResponse(
            path=export_path,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        logger.error(f"[Export Error] {e}")
        raise HTTPException(status_code=500, detail="Export failed. Please try again later.")
