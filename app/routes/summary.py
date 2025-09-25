# === app/routes/summary.py ===
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.summary import SummaryRequest, SummaryResponse

router = APIRouter(tags=["Summarization"])


@router.post("/", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def summarize_transcript(
    payload: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a summary for a given transcript.
    """
    # TODO: fetch transcript text from DB by payload.transcript_id
    # transcript = ...
    # if not transcript:
    #     raise HTTPException(status_code=404, detail="Transcript not found")

    # TODO: call your summarization logic (e.g., GPT)
    summary_text = ""  # placeholder

    return SummaryResponse(
        transcript_id=payload.transcript_id,
        summary=summary_text,
    )
