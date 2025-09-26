import logging
import os
import secrets  # [^3]

import redis
from dotenv import load_dotenv

# Load environment variables from .env (for local/dev convenience)  [^4]
load_dotenv()

# Module-level logger
t_logger = logging.getLogger(__name__)


class Config:
    """
    Centralized configuration for EchoScript.AI, driven entirely by environment variables.
    """

    def __init__(self):
        # — Application settings —
        self.APP_NAME: str = os.getenv("APP_NAME", "EchoScript.AI")
        self.DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")

        # — Whisper defaults —
        self.DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
        self.WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "medium")

        # — API keys and tokens —
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.HF_TOKEN: str = os.getenv("HF_TOKEN", "")
        self.STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
        self.STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "*")

        # — JWT configuration —
        env_secret = os.getenv("JWT_SECRET_KEY")
        if env_secret:
            # Use the explicitly provided secret
            self.JWT_SECRET_KEY: str = env_secret
        elif self.DEBUG:
            # DEBUG fallback: generate a strong random key at runtime  [^1]
            self.JWT_SECRET_KEY = secrets.token_urlsafe(32)
            t_logger.warning(
                "JWT_SECRET_KEY not set; generated a random key for DEBUG mode"
            )
        else:
            # In production, fail fast if no secret is provided  [^2]
            raise RuntimeError(
                "Environment variable JWT_SECRET_KEY is required in production"
            )
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

        # — SMTP settings for email —
        self.EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "")
        self.EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
        self.SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

        # — Persistence and caching —
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # — CORS origins —
        origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
        if origins and origins != "*":
            self.CORS_ALLOW_ORIGINS: list[str] = [o.strip() for o in origins.split(",")]
        else:
            self.CORS_ALLOW_ORIGINS: list[str] = ["*"]

        # — File system paths —
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.BASE_DIR: str = base_dir
        self.UPLOAD_FOLDER: str = os.getenv(
            "UPLOAD_FOLDER", os.path.join(base_dir, "static", "uploads")
        )
        self.STORAGE_DIR: str = os.getenv(
            "STORAGE_DIR", os.path.join(base_dir, "transcripts")
        )
        self.EXPORT_DIR: str = os.getenv(
            "EXPORT_DIR", os.path.join(base_dir, "exports")
        )
        self.LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(base_dir, "logs"))

        # — Upload settings —
        self.ALLOWED_EXTENSIONS: set[str] = {
            ".mp3",
            ".wav",
            ".m4a",
            ".mp4",
            ".flac",
            ".ogg",
            ".webm",
            ".mov",
        }


# Instantiate global configuration
config = Config()

# Initialize Redis client (properly handling None) and log the outcome
redis_client: redis.Redis | None = None

try:
    client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
    client.ping()
    redis_client = client
    t_logger.info(f"Connected to Redis at {config.REDIS_URL}")
except Exception as e:
    t_logger.warning(f"Could not connect to Redis at {config.REDIS_URL}: {e}")
