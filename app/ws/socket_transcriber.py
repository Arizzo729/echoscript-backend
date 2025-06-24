# ---- EchoScript.AI: ws/socket_transcriber.py ----

import tempfile
from fastapi import WebSocket
from app.utils.logger import logger
import torch
import whisperx
import numpy as np
import soundfile as sf
import noisereduce as nr
import librosa
import os
from dotenv import load_dotenv

# ---- Load Env and Set OpenAI API Key ----
load_dotenv()

# ---- Adaptive GPU/CPU Selection ----
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "float32"

# ---- Load WhisperX model with safer fallback ----
try:
    whisper_model = whisperx.load_model("medium", device=device, compute_type=compute_type)
    logger.info(f"✅ WhisperX 'medium' model loaded ({device}, {compute_type})")
except Exception as e:
    logger.error(f"❌ WhisperX model failed to load: {e}")
    whisper_model = None

# ---- Parameters ----
SAMPLING_RATE = 16000
CHUNK_DURATION = 5  # seconds
BUFFER_SIZE = SAMPLING_RATE * CHUNK_DURATION

# ---- WebSocket Streaming Handler ----
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_buffer = bytearray()
    logger.info("🎙️ WebSocket transcription session started")

    try:
        while True:
            try:
                chunk = await websocket.receive_bytes()
            except Exception as recv_error:
                logger.warning(f"⚠️ WebSocket receive failed: {recv_error}")
                break

            audio_buffer.extend(chunk)

            if len(audio_buffer) >= BUFFER_SIZE * 2:  # 16-bit PCM = 2 bytes/sample
                await websocket.send_json({"status": "processing"})

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
                    np_audio = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    denoised = nr.reduce_noise(y=np_audio, sr=SAMPLING_RATE)
                    sf.write(tmp_file.name, denoised, SAMPLING_RATE)

                    try:
                        if whisper_model:
                            result = whisper_model.transcribe(tmp_file.name, language='auto')
                            lang = result.get("language", "unknown")
                            raw_text = result.get("text", "").strip()

                            cleaned_text = (await ai_enhance_transcript(raw_text)) or "[No clear speech]"

                            await websocket.send_json({
                                "text": cleaned_text,
                                "language": lang
                            })
                            logger.debug(f"🧠 Transcribed: {cleaned_text[:60]}...")
                        else:
                            await websocket.send_json({"text": "[Transcription engine unavailable.]", "error": True})
                    except Exception as transcribe_error:
                        logger.warning(f"⚠️ WhisperX failed on buffer: {transcribe_error}")
                        await websocket.send_json({"text": "[Unclear speech detected.]", "error": True})

                    audio_buffer.clear()

    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await websocket.close(code=1011)
    finally:
        logger.info("🔌 WebSocket transcription session ended")

# ---- GPT-Based AI Transcript Enhancement ----
async def ai_enhance_transcript(text: str) -> str:
    if not text.strip():
        return "[No recognizable speech]"

    import openai
    from app.config import Config

    openai.api_key = Config.OPENAI_API_KEY
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a speech comprehension assistant trained to clean and clarify transcribed speech, especially with accents or impairments. Do not change speaker meaning or tone."
                },
                {
                    "role": "user",
                    "content": f"Clean and clarify this transcription:\n\n{text}"
                }
            ],
            temperature=0.4,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"GPT enhancement failed: {e}")
        return text
