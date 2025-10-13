# app/utils/file_helpers.py
import os
import time
from pathlib import Path

from app.core.settings import settings

def save_transcript_file(content: str, user_id: int) -> str:
    """
    Saves transcript content to a file in the STORAGE_DIR.

    The filename includes the user_id and a timestamp to ensure uniqueness.
    Returns the name of the created file.
    """
    storage_dir = Path(settings.STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    filename = f"transcript_{user_id}_{timestamp}.txt"
    filepath = storage_dir / filename

    filepath.write_text(content, encoding="utf-8")
    return filename

def load_transcript_file(filename: str) -> str:
    """
    Loads the content of a specific transcript file from the STORAGE_DIR.
    Raises FileNotFoundError if the file does not exist.
    """
    filepath = Path(settings.STORAGE_DIR) / filename
    if not filepath.is_file():
        raise FileNotFoundError(f"Transcript file not found: {filename}")
    
    return filepath.read_text(encoding="utf-8")

def list_transcripts(user_id: int) -> list[str]:
    """
    Lists all transcript filenames for a given user_id in the STORAGE_DIR.
    """
    storage_dir = Path(settings.STORAGE_DIR)
    if not storage_dir.is_dir():
        return []

    files = []
    for f in storage_dir.iterdir():
        if f.name.startswith(f"transcript_{user_id}_") and f.name.endswith(".txt"):
            files.append(f.name)
            
    return sorted(files, reverse=True)