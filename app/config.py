# === config.py — EchoScript.AI Advanced Configuration ===

import os
import redis
from pathlib import Path
from dotenv import load_dotenv

# === Load .env ===
load_dotenv()

# === Base Directory ===
BASE_DIR = Path(__file__).resolve().parent

# === Runtime Directories ===
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
STORAGE_DIR = BASE_DIR / "transcripts"
EXPORT_DIR = BASE_DIR / "exports"
LOG_DIR = BASE_DIR / "logs"

# === Ensure Runtime Directories Exist ===
for path in [UPLOAD_FOLDER, STORAGE_DIR, EXPORT_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# === Config Class ===
class Config:
    def __init__(self):
        # App
        self.APP_NAME = "EchoScript.AI"
        self.DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

        # API Keys
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.HF_API_TOKEN = os.getenv("HF_API_TOKEN")

        # Auth
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

        # Redis & DB
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

        # File Paths
        self.UPLOAD_FOLDER = UPLOAD_FOLDER
        self.STORAGE_DIR = STORAGE_DIR
        self.EXPORT_DIR = EXPORT_DIR
        self.LOG_DIR = LOG_DIR

        # Upload config
        self.ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "flac", "webm", "ogg"}

    def print_summary(self):
        print(f"[CONFIG] App: {self.APP_NAME}")
        print(f"[CONFIG] Debug: {self.DEBUG}")
        print(f"[CONFIG] Log Level: {self.LOG_LEVEL}")
        print(f"[CONFIG] Redis: {self.REDIS_URL}")
        print(f"[CONFIG] Database: {self.DATABASE_URL}")
        print(f"[CONFIG] Upload Folder: {self.UPLOAD_FOLDER}")
        if not self.OPENAI_API_KEY:
            print("[⚠️  WARNING] OPENAI_API_KEY is not set!")
        if not self.JWT_SECRET_KEY:
            print("[⚠️  WARNING] JWT_SECRET_KEY is not set!")

# === Redis Helper ===
def get_redis_client(config: Config):
    try:
        client = redis.Redis.from_url(config.REDIS_URL)
        client.ping()
        return client
    except Exception as e:
        print(f"[REDIS ⚠️ ] Connection failed: {e}")
        return None

# === Instantiate Config ===
config = Config()
redis_client = get_redis_client(config)

