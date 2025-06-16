# app/routes/profile.py — EchoScript.AI Avatar Upload API

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from uuid import uuid4
from PIL import Image
import os, base64

router = APIRouter(prefix="/api/profile", tags=["Profile"])

# === Constants ===
AVATAR_DIR = Path("static/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# === Upload Avatar (Form file or base64) ===
@router.post("/upload-avatar")
async def upload_avatar(
    user_id: str = Form(...),
    file: UploadFile = File(None),
    base64_img: str = Form(None)
):
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user ID.")

    filename = f"{user_id}_{uuid4().hex[:8]}.png"
    path = AVATAR_DIR / filename

    try:
        # Option A: UploadFile (raw file upload)
        if file:
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Unsupported file type.")

            contents = await file.read()
            with open(path, "wb") as f:
                f.write(contents)

        # Option B: base64 string
        elif base64_img:
            try:
                header, encoded = base64_img.split(",", 1)
                image_data = base64.b64decode(encoded)
                with open(path, "wb") as f:
                    f.write(image_data)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid base64 image format.")

        else:
            raise HTTPException(status_code=400, detail="No file or base64 provided.")

        # Optional: Verify image integrity
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception:
            os.remove(path)
            raise HTTPException(status_code=400, detail="Invalid image file.")

        return JSONResponse({
            "status": "success",
            "avatar_url": f"/static/avatars/{filename}"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

