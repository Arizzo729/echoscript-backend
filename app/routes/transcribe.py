from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Query

# relative prefix (no /api)
router = APIRouter(prefix="/transcribe", tags=["transcribe"])

@router.post("/")
async def transcribe(file: UploadFile = File(...), language: str = Query("en")):
    # Minimal acceptor so UI stops 404-ing and can show queued state
    return {
        "job_id": uuid4().hex,
        "status": "queued",
        "filename": file.filename,
        "language": language,
    }


