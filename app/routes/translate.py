from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.translate import TranslateRequest, TranslateResponse

router = APIRouter(tags=["Translation"])


@router.post("/", response_model=TranslateResponse, status_code=status.HTTP_200_OK)
async def translate_text(
    payload: TranslateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Translate a transcript into a target language.
    """
    # TODO: fetch transcript from DB using payload.transcript_id
    # transcript = ...
    # if not transcript:
    #     raise HTTPException(status_code=404, detail="Transcript not found")

    # TODO: perform translation (e.g., via GPT or external API)
    translated_content = ""  # placeholder

    return TranslateResponse(
        transcript_id=payload.transcript_id,
        target_language=payload.target_language,
        content=translated_content,
    )
