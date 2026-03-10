import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["User"])

UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Max file size: 2MB
    MAX_SIZE = 2 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Image size exceeds 2MB limit")
    
    # Reset file pointer after reading for saving
    await file.seek(0)

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"{current_user.id}_{int(datetime.now().timestamp())}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file locally
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user in database
    avatar_url = f"http://localhost:8000/api/v1/user/avatar/raw/{filename}"
    current_user.avatar_url = avatar_url
    current_user.avatar_uploaded_at = datetime.now()
    db.commit()
    
    return {"avatar_url": avatar_url}

@router.get("/avatar/raw/{filename}")
async def get_raw_avatar(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Avatar not found")
    from fastapi.responses import FileResponse
    return FileResponse(file_path)
