# === app/config.py === (adjusted to allow missing JWT_SECRET_KEY in DEBUG mode)

import os
from dotenv import load_dotenv
from typing import List, Optional
import logging
import redis

load_dotenv()
logger = logging.getLogger(__name__)

class Config:
    """
    Centralized configuration for EchoScript.AI,
    driven entirely by environment variables.
    """

    def __init__(self):
        # Basic settings
        self.APP_NAME = os.getenv("APP_NAME", "EchoScript.AI")
        self.DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

        # Whisper defaults
        self.DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
        self.WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")

        # External services
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
        self.STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # JWT – allow default in DEBUG
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        if not self.JWT_SECRET_KEY:
            if self.DEBUG:
                self.JWT_SECRET_KEY = "supersecret"
                logger.warning(
                    "JWT_SECRET_KEY not set; using insecure default 'supersecret' in DEBUG mode"
                )
            else:
                raise RuntimeError("Environment variable JWT_SECRET_KEY is required in production")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

        # Redis & Database
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

        # CORS
        origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
        self.CORS_ALLOW_ORIGINS = [o.strip() for o in origins.split(",") if o.strip()]

        # Paths
        base = os.path.dirname(os.path.abspath(__file__))
        self.BASE_DIR = base
        self.UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(base, "static", "uploads"))
        self.STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(base, "transcripts"))
        self.EXPORT_DIR = os.getenv("EXPORT_DIR", os.path.join(base, "exports"))
        self.LOG_DIR = os.getenv("LOG_DIR", os.path.join(base, "logs"))

        # Upload settings
        self.ALLOWED_EXTENSIONS = {"mp3","wav","m4a","mp4","flac","ogg","webm","mov"}

# single instance
Config = Config()

# Redis client
try:
    redis_client: Optional[redis.Redis] = redis.Redis.from_url(Config.REDIS_URL)
    redis_client.ping()
except Exception as e:
    redis_client = None
    logger.warning(f"Could not connect to Redis at {Config.REDIS_URL}: {e}")

