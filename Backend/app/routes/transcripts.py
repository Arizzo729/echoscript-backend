from typing import List

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.utils.file_helpers import list_transcripts

router = APIRouter()


@router.get(
    "/",
    response_model=List[str],
    summary="List all saved transcripts for the current user",
)
async def get_transcripts(current_user=Depends(get_current_user)) -> List[str]:
    """
    Retrieve a list of transcript filenames saved for the authenticated user.
    Filenames follow the pattern 'transcript_{user_id}_{timestamp}.txt'.
    """
    files = list_transcripts(current_user.id)
    return files


# In your main.py, register this router:
# from app.routes.transcripts import router as transcripts_router
# app.include_router(transcripts_router, prefix="/api/transcripts", tags=["Transcripts"])
