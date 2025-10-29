import os
import time

from app.config import config

# Ensure storage directory exists
os.makedirs(config.STORAGE_DIR, exist_ok=True)


def save_transcript_file(content: str, user_id: int) -> str:
    """
    Save the transcript text to a file in STORAGE_DIR.
    Filenames are prefixed by user_id and timestamp. Returns the filename.
    """
    timestamp = int(time.time())
    filename = f"transcript_{user_id}_{timestamp}.txt"
    filepath = os.path.join(config.STORAGE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def load_transcript_file(filename: str) -> str:
    """
    Load and return the content of a transcript file.
    """
    filepath = os.path.join(config.STORAGE_DIR, filename)
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Transcript file not found: {filename}")
    with open(filepath, encoding="utf-8") as f:
        return f.read()


def list_transcripts(user_id: int) -> list[str]:
    """
    List all transcript filenames for a given user_id.
    """
    files = []
    for fname in os.listdir(config.STORAGE_DIR):
        if fname.startswith(f"transcript_{user_id}_") and fname.endswith(".txt"):
            files.append(fname)
    return sorted(files)


__all__ = [
    "save_transcript_file",
    "load_transcript_file",
    "list_transcripts",
]
