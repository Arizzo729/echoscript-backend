# ---- EchoScript.AI: utils/file_helpers.py ----

import os
import uuid
from typing import Optional, List
from app.config import Config
from app.utils.logger import logger

# === Ensure transcript storage directory exists ===
os.makedirs(Config.STORAGE_DIR, exist_ok=True)

# === Save Transcript to Disk ===
def save_transcript_file(content: str, user_id: str = "anonymous") -> Optional[str]:
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}.txt"
    filepath = os.path.join(Config.STORAGE_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"[File] ✅ Saved transcript @ {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"[File Error] ❌ Saving failed: {e}")
        return None

# === Load Transcript File by Path ===
def load_transcript(filepath: str) -> Optional[str]:
    if not os.path.isfile(filepath):
        logger.warning(f"[File] ⚠️ Missing file: {filepath}")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"[File] 📂 Loaded transcript: {filepath}")
        return content
    except Exception as e:
        logger.error(f"[File Error] ❌ Loading failed: {e}")
        return None

# === List Transcript Files (Optionally Filtered by User ID) ===
def list_transcripts(user_id: Optional[str] = None) -> List[str]:
    try:
        files = os.listdir(Config.STORAGE_DIR)
        filtered = [
            f for f in files
            if f.endswith(".txt") and (user_id in f if user_id else True)
        ]
        logger.info(f"[File] 📄 {len(filtered)} transcript(s) found for user='{user_id or 'all'}'")
        return filtered
    except Exception as e:
        logger.error(f"[File Error] ❌ Listing failed: {e}")
        return []
