# config.py — EchoScript.AI Advanced Configuration

import os
import redis
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load .env vars

# === Base Directory ===
BASE_DIR = Path(__file__).resolve().parent

# === Runtime Directories ===
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
STORAGE_DIR = BASE_DIR / "transcripts"
EXPORT_DIR = BASE_DIR / "exports"
LOG_DIR = BASE_DIR / "logs"

# === Core Configuration ===
class Config:
    # App
    APP_NAME = "EchoScript.AI"
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HF_API_TOKEN = os.getenv("HF_API_TOKEN")

    # Auth
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # Redis & DB
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

    # Paths
    UPLOAD_FOLDER = UPLOAD_FOLDER
    STORAGE_DIR = STORAGE_DIR
    EXPORT_DIR = EXPORT_DIR
    LOG_DIR = LOG_DIR

    # Upload config
    ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "flac", "webm", "ogg"}

    @staticmethod
    def print_summary():
        print(f"[CONFIG] Debug: {Config.DEBUG}")
        print(f"[CONFIG] Redis: {Config.REDIS_URL}")
        print(f"[CONFIG] DB: {Config.DATABASE_URL}")
        if not Config.OPENAI_API_KEY:
            print("[⚠️  WARNING] OPENAI_API_KEY is not set!")

# === Ensure directories exist ===
for path in [UPLOAD_FOLDER, STORAGE_DIR, EXPORT_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# === Redis Client Initialization ===
try:
    redis_client = redis.Redis.from_url(Config.REDIS_URL)
    redis_client.ping()  # Confirm connectivity
except Exception as e:
    redis_client = None
    print(f"[REDIS ⚠️ ] Connection failed: {e}")
