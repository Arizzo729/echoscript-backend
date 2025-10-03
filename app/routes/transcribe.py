# app/routes/transcribe.py
import os
import shutil
import tempfile
import uuid
from typing import Optional

# app/routes/transcribe.py
from fastapi import APIRouter, UploadFile, File
router = APIRouter()

@router.post("")
async def transcribe(file: UploadFile = File(...)):
    # stub so frontend can proceed; replace with Whisper handler
    return {"ok": True, "filename": file.filename, "text": "(transcription stub)"}

