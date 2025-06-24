from fastapi import APIRouter, UploadFile, File, HTTPException
from faster_whisper import WhisperModel
from dotenv import load_dotenv
import tempfile
import os
import shutil
import logging
import moviepy.editor as mp
import torch

load_dotenv()
logger = logging.getLogger("echoscript")

router = APIRouter()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)

@router.post("/video-upload")
async def upload_video(file: UploadFile = File(...), language: str = "en", translate: bool = False):
    try:
        # Save uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(await file.read())
            video_path = tmp_video.name

        logger.info(f"Saved video: {video_path}")

        # Extract audio to a temp .wav file
        audio_path = video_path.replace(".mp4", ".wav")
        clip = mp.VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, codec='pcm_s16le')  # Uncompressed

        logger.info(f"Extracted audio: {audio_path}")

        # Transcribe using faster-whisper
        segments, info = model.transcribe(audio_path, language=language, beam_size=5, task="translate" if translate else "transcribe")

        # Construct transcript text
        transcript = "\n".join([seg.text for seg in segments])

        logger.info(f"Transcription done")

        return {
            "language": info.language,
            "duration": info.duration,
            "transcript": transcript,
        }

    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process video")

    finally:
        # Cleanup temp files
        for path in [video_path, audio_path]:
            if os.path.exists(path):
                os.remove(path)
