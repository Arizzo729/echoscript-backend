import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User, Transcript
from app.config import config

router = APIRouter(prefix="/transcribe", tags=["transcribe"])


@router.post("/")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Query("en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and transcribe an audio/video file.
    Automatically saves the completed transcript to the user's account.
    """
    try:
        # Import transcription logic from asgi_dev
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from asgi_dev import _transcribe_file, STORAGE_DIR
        
        # Generate unique ID for this file
        job_id = str(uuid4())
        ext = Path(file.filename).suffix.lower() or ".mp3"
        storage_filename = f"{job_id}{ext}"
        file_path = STORAGE_DIR / storage_filename
        
        # Save the uploaded file
        file_size = 0
        with file_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                file_size += len(chunk)
        
        # Perform transcription
        transcript_text = _transcribe_file(file_path, language=language)
        
        # Create transcript record in database
        db_transcript = Transcript(
            user_id=current_user.id,
            title=file.filename or f"Transcript {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            original_filename=file.filename,
            storage_filename=storage_filename,
            content=transcript_text,
            duration=None,  # Could be calculated from audio metadata if needed
            file_size=file_size,
            language=language if language != "auto" else "en",
            status="completed"
        )
        
        db.add(db_transcript)
        db.commit()
        db.refresh(db_transcript)
        
        # Return the transcript data
        return {
            "status": "success",
            "job_id": job_id,
            "transcript_id": db_transcript.id,
            "filename": file.filename,
            "transcript": transcript_text,
            "language": language,
            "message": "Transcript saved to your account"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Clean up file if it was created
        if 'file_path' in locals() and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
