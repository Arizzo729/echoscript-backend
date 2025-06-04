# app/routes/profile.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path
from PIL import Image
import base64

router = APIRouter()

AVATAR_DIR = Path("static/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/api/profile/upload-avatar")
async def upload_avatar(user_id: str = Form(...), file: UploadFile = File(None), base64: str = Form(None)):
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}.png"
    path = AVATAR_DIR / filename

    if file:
        contents = await file.read()
        with open(path, "wb") as f:
            f.write(contents)
    elif base64:
        try:
            header, encoded = base64.split(",", 1)
            image_data = base64.b64decode(encoded)
            with open(path, "wb") as f:
                f.write(image_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image format.")
    else:
        raise HTTPException(status_code=400, detail="No file or base64 provided.")

    return JSONResponse({"status": "success", "avatar_url": f"/static/avatars/{filename}"})
