from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

from app.dependencies import get_current_user, get_db
from app.models import Transcript, User
from app.utils.file_helpers import list_transcripts, load_transcript_file, save_transcript_file
from app.config import config

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


class TranscriptResponse(BaseModel):
    id: int
    title: str
    original_filename: Optional[str]
    storage_filename: str
    content: Optional[str]
    duration: Optional[int]
    file_size: Optional[int]
    language: Optional[str]
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TranscriptCreate(BaseModel):
    title: str
    original_filename: Optional[str] = None
    content: str
    duration: Optional[int] = None
    file_size: Optional[int] = None
    language: Optional[str] = "en"


class TranscriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    duration: Optional[int] = None
    language: Optional[str] = None


@router.get(
    "/",
    response_model=list[TranscriptResponse],
    summary="List all transcripts for the current user",
)
async def get_transcripts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[TranscriptResponse]:
    """
    Retrieve all transcripts for the authenticated user with full metadata.
    """
    transcripts = db.query(Transcript).filter(
        Transcript.user_id == current_user.id
    ).order_by(Transcript.created_at.desc()).all()
    
    return [
        TranscriptResponse(
            id=t.id,
            title=t.title,
            original_filename=t.original_filename,
            storage_filename=t.storage_filename,
            content=t.content[:200] + "..." if t.content and len(t.content) > 200 else t.content,
            duration=t.duration,
            file_size=t.file_size,
            language=t.language,
            status=t.status,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else "",
        )
        for t in transcripts
    ]


@router.get(
    "/{transcript_id}",
    response_model=TranscriptResponse,
    summary="Get a single transcript by ID",
)
async def get_transcript(
    transcript_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TranscriptResponse:
    """
    Retrieve a specific transcript by ID with full content.
    """
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return TranscriptResponse(
        id=transcript.id,
        title=transcript.title,
        original_filename=transcript.original_filename,
        storage_filename=transcript.storage_filename,
        content=transcript.content,
        duration=transcript.duration,
        file_size=transcript.file_size,
        language=transcript.language,
        status=transcript.status,
        created_at=transcript.created_at.isoformat() if transcript.created_at else "",
        updated_at=transcript.updated_at.isoformat() if transcript.updated_at else "",
    )


@router.post(
    "/",
    response_model=TranscriptResponse,
    summary="Create a new transcript",
)
async def create_transcript(
    data: TranscriptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TranscriptResponse:
    """
    Create a new transcript with metadata.
    """
    import time
    
    storage_filename = f"transcript_{current_user.id}_{int(time.time())}.txt"
    
    actual_filename = save_transcript_file(data.content, current_user.id, storage_filename)
    
    transcript = Transcript(
        user_id=current_user.id,
        title=data.title,
        original_filename=data.original_filename,
        storage_filename=actual_filename,
        content=data.content,
        duration=data.duration,
        file_size=data.file_size if data.file_size else len(data.content),
        language=data.language,
        status="completed",
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    return TranscriptResponse(
        id=transcript.id,
        title=transcript.title,
        original_filename=transcript.original_filename,
        storage_filename=transcript.storage_filename,
        content=transcript.content,
        duration=transcript.duration,
        file_size=transcript.file_size,
        language=transcript.language,
        status=transcript.status,
        created_at=transcript.created_at.isoformat() if transcript.created_at else "",
        updated_at=transcript.updated_at.isoformat() if transcript.updated_at else "",
    )


@router.put(
    "/{transcript_id}",
    response_model=TranscriptResponse,
    summary="Update a transcript",
)
async def update_transcript(
    transcript_id: int,
    data: TranscriptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TranscriptResponse:
    """
    Update an existing transcript's title, content, or metadata.
    """
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    if data.title is not None:
        transcript.title = data.title
    if data.content is not None:
        transcript.content = data.content
        transcript.file_size = len(data.content)
        save_transcript_file(data.content, current_user.id, transcript.storage_filename)
    if data.duration is not None:
        transcript.duration = data.duration
    if data.language is not None:
        transcript.language = data.language
    
    db.commit()
    db.refresh(transcript)
    
    return TranscriptResponse(
        id=transcript.id,
        title=transcript.title,
        original_filename=transcript.original_filename,
        storage_filename=transcript.storage_filename,
        content=transcript.content,
        duration=transcript.duration,
        file_size=transcript.file_size,
        language=transcript.language,
        status=transcript.status,
        created_at=transcript.created_at.isoformat() if transcript.created_at else "",
        updated_at=transcript.updated_at.isoformat() if transcript.updated_at else "",
    )


@router.delete(
    "/{transcript_id}",
    summary="Delete a transcript",
)
async def delete_transcript(
    transcript_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a transcript and its associated file.
    """
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    try:
        filepath = os.path.join(config.STORAGE_DIR, transcript.storage_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Failed to delete file: {e}")
    
    db.delete(transcript)
    db.commit()
    
    return {"ok": True, "message": "Transcript deleted successfully"}
