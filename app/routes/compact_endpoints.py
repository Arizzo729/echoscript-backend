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
# These compatibility endpoints redirect old API paths to the current v1 prefixes.
# The redirect targets use /api/v1 so they resolve correctly whether the router
# is mounted under /api/v1 or only /api (as in some dev setups).
@router.post("/api/auth/signin")
async def api_signin_alias():
    # 307 preserves method/body; fetch follows automatically
    return RedirectResponse(url="/api/v1/auth/login", status_code=307)

@router.post("/auth/signin")
async def bare_signin_alias():
    return RedirectResponse(url="/api/v1/auth/login", status_code=307)

# also alias signup just in case some clients hit it directly
@router.post("/api/auth/signup")
async def api_signup_alias():
    return RedirectResponse(url="/api/v1/auth/signup", status_code=307)

@router.post("/auth/signup")
async def bare_signup_alias():
    return RedirectResponse(url="/api/v1/auth/signup", status_code=307)

# ---------- Helpers (shared impls) ----------
async def _transcribe_impl(file: UploadFile, language: Optional[str] = "en"):
    """
    Transcription endpoint that integrates with asgi_dev.py if available,
    otherwise provides informative placeholder response.
    """
    import sys
    import tempfile
    import uuid
    from pathlib import Path
    from faster_whisper import WhisperModel
    
    try:
        data = await file.read()
        file_size_mb = len(data) / (1024 * 1024)
        
        # Save uploaded file temporarily
        ext = Path(file.filename).suffix.lower() or ".bin"
        temp_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}{ext}"
        
        try:
            with temp_path.open("wb") as f:
                f.write(data)
            
            # Use Whisper directly for transcription
            model = WhisperModel("small", device="cpu", compute_type="int8")
            segments_raw, info = model.transcribe(
                str(temp_path),
                beam_size=5,
                best_of=1,
                language=language if language != "auto" else None,
                temperature=0.0,
                condition_on_previous_text=True,
            )
            
            # Extract segments with timing information
            segments = []
            full_text_parts = []
            for seg in segments_raw:
                text = getattr(seg, "text", "").strip()
                if text:
                    segments.append({
                        "start": getattr(seg, "start", 0.0),
                        "end": getattr(seg, "end", 0.0),
                        "text": text
                    })
                    full_text_parts.append(text)
            
            transcript_text = " ".join(full_text_parts).strip() or "(empty transcript)"
            
            return JSONResponse({
                "transcript": transcript_text,
                "summary": None,
                "sentiment": None,
                "language": getattr(info, 'language', language or 'en'),
                "filename": file.filename,
                "file_size_mb": round(file_size_mb, 2),
                "segments": segments,
                "status": "completed"
            })
        finally:
            # Clean up temp file
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete temp file {temp_path}: {e}")
    
    except Exception as e:
        import traceback
        print(f"Transcription error: {e}")
        traceback.print_exc()
        
        # Return error response instead of failing completely
        return JSONResponse(
            {
                "error": f"Transcription failed: {str(e)}",
                "filename": file.filename,
                "status": "error"
            },
            status_code=500
        )


async def _video_task_impl(
    file: UploadFile | None = None,
    task_type: Optional[str] = "transcription",
    language: Optional[str] = "en",
):
    """
    Video processing endpoint that extracts audio and processes it.
    Supports both transcription and subtitle generation.
    """
    if file is None:
        return JSONResponse({"error": "No file provided"}, status_code=400)
    
    import tempfile
    import uuid
    from pathlib import Path
    from faster_whisper import WhisperModel
    
    temp_video_path = None
    temp_audio_path = None
    
    try:
        # Read file data
        data = await file.read()
        file_size_mb = len(data) / (1024 * 1024)
        
        # Save video temporarily
        ext = Path(file.filename).suffix.lower() or ".mp4"
        temp_video_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}{ext}"
        temp_audio_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.wav"
        
        # Save uploaded video
        with temp_video_path.open("wb") as f:
            f.write(data)
        
        # Extract audio using ffmpeg
        try:
            import ffmpeg
            (
                ffmpeg
                .input(str(temp_video_path))
                .output(str(temp_audio_path), ac=1, ar=16000, format="wav")
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )
            audio_path = temp_audio_path
        except Exception as e:
            print(f"FFmpeg audio extraction failed: {e}. Using video directly.")
            # If ffmpeg fails, try to process video directly
            audio_path = temp_video_path
        
        # Use Whisper for transcription
        model = WhisperModel("small", device="cpu", compute_type="int8")
        
        segments_raw, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            best_of=1,
            language=language if language != "auto" else None,
            temperature=0.0,
            condition_on_previous_text=True,
        )
        
        # Extract segments with timing information
        segments = []
        full_text_parts = []
        for seg in segments_raw:
            text = getattr(seg, "text", "").strip()
            if text:
                segments.append({
                    "start": getattr(seg, "start", 0.0),
                    "end": getattr(seg, "end", 0.0),
                    "text": text
                })
                full_text_parts.append(text)
        
        transcript_text = " ".join(full_text_parts).strip() or "(empty transcript)"
        
        # Return based on task type
        if task_type == "subtitles":
            # Generate SRT format subtitles
            srt_lines = []
            for i, seg in enumerate(segments, 1):
                start_time = _format_timestamp(seg["start"])
                end_time = _format_timestamp(seg["end"])
                srt_lines.append(f"{i}\n{start_time} --> {end_time}\n{seg['text']}\n")
            
            subtitles = "\n".join(srt_lines)
            return JSONResponse({
                "subtitles": subtitles,
                "language": getattr(info, 'language', language or 'en'),
                "format": "srt",
                "filename": file.filename,
                "status": "completed"
            })
        else:
            # Return transcription
            return JSONResponse({
                "transcript": transcript_text,
                "summary": None,
                "sentiment": None,
                "language": getattr(info, 'language', language or 'en'),
                "filename": file.filename,
                "file_size_mb": round(file_size_mb, 2),
                "segments": segments,
                "status": "completed"
            })
    
    except Exception as e:
        import traceback
        print(f"Error processing video: {e}")
        traceback.print_exc()
        
        return JSONResponse(
            {
                "error": f"Video processing failed: {str(e)}",
                "filename": file.filename if file else "unknown",
                "status": "error"
            },
            status_code=500
        )
    
    finally:
        # Clean up temp files
        try:
            if temp_video_path and temp_video_path.exists():
                temp_video_path.unlink()
        except Exception as e:
            print(f"Warning: Could not delete temp video file: {e}")
        try:
            if temp_audio_path and temp_audio_path.exists() and temp_audio_path != temp_video_path:
                temp_audio_path.unlink()
        except Exception as e:
            print(f"Warning: Could not delete temp audio file: {e}")

def _format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

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

# ---------- Submit Transcript ----------
async def _submit_transcript_impl(payload: dict):
    """
    Accepts a transcript payload and persists it.
    Forwards to the usage router's submitTranscript endpoint logic.
    """
    import json
    import uuid
    from app.utils.redis_client import cache
    
    key = f"transcript:{uuid.uuid4().hex}"
    
    try:
        user = payload.get("user_id", "anon")
        file_name = payload.get("fileName", "unknown")
        transcript = payload.get("transcript", "")
        translated = payload.get("translated")
        summary = payload.get("summary")
        sentiment = payload.get("sentiment")
        
        meta = {
            "fileName": file_name,
            "translated": translated,
            "summary": summary,
            "sentiment": sentiment
        }
        
        from datetime import datetime
        
        item = {
            "user_id": user,
            "transcript": transcript,
            "meta": meta,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        cache.set(key, json.dumps(item), ex=3600)
        return JSONResponse({"ok": True, "id": key, "message": "Transcript submitted successfully"})
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": str(e)},
            status_code=500
        )

@router.post("/api/submitTranscript")
async def api_submit_transcript(payload: dict):
    return await _submit_transcript_impl(payload)

@router.post("/submitTranscript")
async def bare_submit_transcript(payload: dict):
    return await _submit_transcript_impl(payload)

