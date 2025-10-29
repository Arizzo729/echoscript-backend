"""
Compat layer so the current frontend stops 404'ing.

Mount this router ONCE with NO prefix in app/main.py:
    from app.routes import compact_endpoints as compat
    app.include_router(compat.router)

It exposes BOTH '/api/*' and bare '/*' paths.
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response, RedirectResponse

# No prefix here; we declare full paths in each route
router = APIRouter(tags=["compat"])

# ---------- Auth aliases ----------
@router.post("/api/auth/signin")
async def api_signin_alias():
    # 307 preserves method/body; fetch follows automatically
    return RedirectResponse(url="/api/auth/login", status_code=307)

@router.post("/auth/signin")
async def bare_signin_alias():
    return RedirectResponse(url="/api/auth/login", status_code=307)

# ---------- Helpers (shared impls) ----------
async def _transcribe_impl(file: UploadFile, language: Optional[str] = "en"):
    data = await file.read()
    return JSONResponse(
        {"text": f"(stub) received {file.filename} ({len(data)} bytes), language={language}"}
    )

async def _video_task_impl(
    file: UploadFile | None = None,
    task_type: Optional[str] = "transcription",
    language: Optional[str] = "en",
):
    return JSONResponse({"status": "queued", "task_id": "stub-1"}, status_code=202)

async def _subtitles_impl(file: UploadFile):
    _ = await file.read()
    vtt = "WEBVTT\n\n00:00.000 --> 00:01.500\n(Stub) EchoScript subtitles ready\n"
    return Response(content=vtt, media_type="text/vtt")

# ---------- Transcribe ----------
@router.post("/api/transcribe")
async def api_transcribe(file: UploadFile = File(...), language: Optional[str] = "en"):
    return await _transcribe_impl(file, language)

@router.post("/transcribe")
async def bare_transcribe(file: UploadFile = File(...), language: Optional[str] = "en"):
    return await _transcribe_impl(file, language)

# Keep old versioned paths working too
@router.post("/api/v1/transcribe")
async def api_v1_transcribe(file: UploadFile = File(...), language: Optional[str] = "en"):
    return await _transcribe_impl(file, language)

@router.post("/v1/transcribe")
async def v1_transcribe(file: UploadFile = File(...), language: Optional[str] = "en"):
    return await _transcribe_impl(file, language)

# ---------- Video task ----------
@router.post("/api/video-task")
async def api_video_task(
    file: UploadFile = File(None),
    task_type: Optional[str] = Form("transcription"),
    language: Optional[str] = Form("en"),
):
    return await _video_task_impl(file, task_type, language)

@router.post("/video-task")
async def bare_video_task(
    file: UploadFile = File(None),
    task_type: Optional[str] = Form("transcription"),
    language: Optional[str] = Form("en"),
):
    return await _video_task_impl(file, task_type, language)

# Support old path some bundles used
@router.post("/api/video/process")
async def api_video_process(
    file: UploadFile = File(None),
    task_type: Optional[str] = Form("transcription"),
    language: Optional[str] = Form("en"),
):
    return await _video_task_impl(file, task_type, language)

# ---------- Subtitles ----------
@router.post("/api/subtitles")
async def api_subtitles(file: UploadFile = File(...)):
    return await _subtitles_impl(file)

@router.post("/subtitles")
async def bare_subtitles(file: UploadFile = File(...)):
    return await _subtitles_impl(file)

