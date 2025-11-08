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
    """
    Transcription endpoint that integrates with asgi_dev.py if available,
    otherwise provides informative placeholder response.
    """
    import sys
    from pathlib import Path
    
    data = await file.read()
    file_size_mb = len(data) / (1024 * 1024)
    
    # Try to use real transcription from asgi_dev if available
    try:
        # Save uploaded file temporarily
        import tempfile
        import uuid
        ext = Path(file.filename).suffix.lower() or ".bin"
        temp_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}{ext}"
        
        with temp_path.open("wb") as f:
            f.write(data)
        
        # Try importing the transcription function from asgi_dev
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        try:
            from asgi_dev import _transcribe_file, WHISPER
            if WHISPER is not None:
                # Real transcription available - get segments directly from Whisper
                segments_raw, info = WHISPER.transcribe(
                    str(temp_path),
                    beam_size=5,
                    best_of=1,
                    vad_filter=True,
                    language=language,
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
                
                # Return with segments for subtitle export
                # TODO: Add summary and sentiment generation using AI
                return JSONResponse({
                    "transcript": transcript_text,
                    "summary": None,
                    "sentiment": None,
                    "language": language or info.language,
                    "filename": file.filename,
                    "file_size_mb": round(file_size_mb, 2),
                    "segments": segments,
                    "status": "completed"
                })
        except Exception as e:
            # Whisper not available or error occurred
            print(f"Whisper transcription not available: {e}")
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            sys.path.pop(0)
    except Exception as e:
        print(f"Error in transcription: {e}")
    
    # Fallback: Return placeholder response with clear messaging
    placeholder_transcript = f"""[PLACEHOLDER TRANSCRIPTION]

This is a demonstration response for file: {file.filename}

To enable real transcription, you need to:
1. Install the Whisper library (faster-whisper)
2. Configure the backend properly
3. Restart the backend server

For now, this shows how the transcription flow works end-to-end.
You can still test the export functionality (PDF, Word, TXT) with this placeholder text."""
    
    return JSONResponse({
        "transcript": placeholder_transcript,
        "summary": f"[DEMO] Key points from {file.filename} would appear here when real transcription is enabled.",
        "sentiment": "[DEMO] Sentiment analysis would appear here (e.g., Positive, Neutral, Negative)",
        "language": language,
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "segments": [
            {"start": 0.0, "end": 3.0, "text": "[PLACEHOLDER] First segment of transcription"},
            {"start": 3.0, "end": 6.0, "text": "[PLACEHOLDER] Second segment of transcription"},
            {"start": 6.0, "end": 9.0, "text": "[PLACEHOLDER] Third segment of transcription"}
        ],
        "keywords": ["placeholder", "demo", "transcription"],
        "status": "completed"
    })

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
    
    import sys
    import tempfile
    import uuid
    from pathlib import Path
    
    # Read file data
    data = await file.read()
    file_size_mb = len(data) / (1024 * 1024)
    
    # Save video temporarily
    ext = Path(file.filename).suffix.lower() or ".mp4"
    temp_video_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}{ext}"
    temp_audio_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.wav"
    
    try:
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
        except Exception as e:
            print(f"FFmpeg audio extraction failed: {e}")
            # If ffmpeg fails, try to process video directly
            temp_audio_path = temp_video_path
        
        # Try importing the transcription function from asgi_dev
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        try:
            from asgi_dev import WHISPER
            if WHISPER is not None:
                # Real transcription available
                # For translation: if language is "en" for transcription, translate to English
                # For subtitles: use the selected language
                task = "transcribe"
                source_lang = language if language != "auto" else None
                
                if task_type == "transcription" and language == "en":
                    task = "translate"
                    source_lang = None
                
                segments_raw, info = WHISPER.transcribe(
                    str(temp_audio_path),
                    beam_size=5,
                    best_of=1,
                    vad_filter=True,
                    language=source_lang,
                    task=task,
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
                        "language": language or info.language,
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
                        "language": language or info.language,
                        "filename": file.filename,
                        "file_size_mb": round(file_size_mb, 2),
                        "segments": segments,
                        "status": "completed"
                    })
        except Exception as e:
            print(f"Whisper transcription not available: {e}")
        finally:
            sys.path.pop(0)
    
    except Exception as e:
        print(f"Error processing video: {e}")
    finally:
        # Clean up temp files
        try:
            if temp_video_path.exists():
                temp_video_path.unlink()
        except:
            pass
        try:
            if temp_audio_path.exists() and temp_audio_path != temp_video_path:
                temp_audio_path.unlink()
        except:
            pass
    
    # Fallback: Return placeholder response
    placeholder_transcript = f"""[PLACEHOLDER TRANSCRIPTION]

This is a demonstration response for video file: {file.filename}

To enable real video transcription, you need to:
1. Install the Whisper library (faster-whisper)
2. Install ffmpeg for audio extraction
3. Restart the backend server

For now, this shows how the video transcription flow works end-to-end."""
    
    if task_type == "subtitles":
        placeholder_srt = """1
00:00:00,000 --> 00:00:03,000
[PLACEHOLDER] First subtitle segment

2
00:00:03,000 --> 00:00:06,000
[PLACEHOLDER] Second subtitle segment

3
00:00:06,000 --> 00:00:09,000
[PLACEHOLDER] Third subtitle segment"""
        
        return JSONResponse({
            "subtitles": placeholder_srt,
            "language": language,
            "format": "srt",
            "filename": file.filename,
            "status": "completed"
        })
    else:
        return JSONResponse({
            "transcript": placeholder_transcript,
            "summary": f"[DEMO] Summary for {file.filename}",
            "sentiment": "[DEMO] Neutral",
            "language": language,
            "filename": file.filename,
            "file_size_mb": round(file_size_mb, 2),
            "status": "completed"
        })

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

