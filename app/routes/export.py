# app/routes/export.py
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.dependencies import get_current_user
from app.utils.export_utils import generate_export_file
from app.utils.logger import logger

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get(
    "/{transcript_id}",
    response_class=FileResponse,
    summary="Export a transcript as txt/pdf/docx/json",
)
def export_transcript(
    transcript_id: int,
    format: Literal["txt", "pdf", "docx", "json"],
    current_user=Depends(get_current_user),
) -> FileResponse:
    try:
        return generate_export_file(transcript_id, format)
    except ValueError as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export"
        )
