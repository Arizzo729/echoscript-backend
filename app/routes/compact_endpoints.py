"""
Compat layer so the current frontend stops 404'ing.

This file declares *absolute* paths starting with /api/* and is mounted
ONCE with NO prefix from main.py (app.include_router(router)).

If/when you normalize your other routers to use relative prefixes and
update the frontend, you can delete this file.
"""
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response

# IMPORTANT: no prefix here; we write full absolute paths in each route.
router = APIRouter(tags=["compat"])


# ---------- Auth alias (optional) ----------
# If your frontend ever hits /api/auth/signin, redirect to /api/auth/login.
from starlette.responses import RedirectResponse


@router.post("/api/auth/signin")
async def compat_signin_redirect():
    # 307 preserves POST + body; browser fetch will follow automatically.
    return RedirectResponse(url="/api/auth/login", status_code=307)


# ---------- Transcribe ----------
@router.post("/api/transcribe")
async def compat_transcribe_api(
    file: UploadFile = File(...),
    language: Optional[str] = "en",
):
    # TODO: replace with real transcription logic or call your service
    data = await file.read()
    return {"text": f"(stub) received {file.filename} ({len(data)} bytes), language={language}"}


# Some older builds may call /api/v1/transcribe or /v1/transcribe.
# Provide them too so nothing 404s while you normalize.
@router.post("/api/v1/transcribe")
async def compat_transcribe_api_v1(
    file: UploadFile = File(...),
    language: Optional[str] = "en",
):
    return await compat_transcribe_api(file=file, language=language)


@router.post("/v1/transcribe")
async def compat_transcribe_v1(
    file: UploadFile = File(...),
    language: Optional[str] = "en",
):
    return await compat_transcribe_api(file=file, language=language)


# ---------- Video task ----------
@router.post("/api/video-task")
async def compat_video_task(
    file: UploadFile = File(None),
    task_type: Optional[str] = Form("transcription"),
    language: Optional[str] = Form("en"),
):
    # TODO: replace with real async job; this unblocks UI now
    return JSONResponse({"status": "queued", "task_id": "stub-1"}, status_code=202)


# Some bundles call /api/video/process; support that too.
@router.post("/api/video/process")
async def compat_video_process(
    file: UploadFile = File(None),
    task_type: Optional[str] = Form("transcription"),
    language: Optional[str] = Form("en"),
):
    return await compat_video_task(file=file, task_type=task_type, language=language)


# ---------- Subtitles ----------
@router.post("/api/subtitles")
async def compat_subtitles(file: UploadFile = File(...)):
    # TODO: replace with real VTT generation
    _ = await file.read()
    vtt = "WEBVTT\n\n00:00.000 --> 00:01.500\n(Stub) EchoScript subtitles ready\n"
    return Response(content=vtt, media_type="text/vtt")

