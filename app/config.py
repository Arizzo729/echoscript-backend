import os
from functools import lru_cache
from typing import Optional

try:
    # Pydantic v2
    from pydantic import BaseSettings, Field
    from pydantic_settings import SettingsConfigDict
except Exception:  # pragma: no cover
    # Fallback to v1 if your env is older
    from pydantic_settings import BaseSettings  # type: ignore
    Field = lambda default=None, **_: default  # type: ignore
    SettingsConfigDict = lambda **_: None  # type: ignore


class Settings(BaseSettings):
    # --- App ---
    ENV: str = Field(default="local")          # local | staging | prod
    DEBUG: bool = Field(default=True)
    GIT_SHA: str = Field(default="local")

    # --- API / CORS ---
    API_ALLOWED_ORIGINS: str = Field(default="*")  # comma-separated or "*"

    # --- Email (SMTP) ---
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_STARTTLS: bool = Field(default=True)
    SMTP_FROM: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    CONTACT_TO_EMAIL: Optional[str] = None
    OWNER_EMAIL: Optional[str] = None

    # --- Redis ---
    REDIS_ENABLED: bool = Field(default=True)
    REDIS_URL: Optional[str] = None  # e.g. redis://:password@host:port/0

    # --- JWT / Auth ---
    JWT_SECRET_KEY: Optional[str] = Field(default=None)
    JWT_ALGORITHM: str = Field(default="HS256")

    # --- Database ---
    DATABASE_URL: Optional[str] = Field(default=None)

    # --- AI Integrations ---
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    HF_TOKEN: Optional[str] = Field(default=None)

    # --- Payments ---
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None)
    STRIPE_PRICE_PRO: Optional[str] = Field(default=None)
    STRIPE_PRICE_PREMIUM: Optional[str] = Field(default=None)
    STRIPE_PRICE_EDU: Optional[str] = Field(default=None)
    FRONTEND_URL: Optional[str] = Field(default="http://localhost:5000")

    # --- File Storage ---
    UPLOAD_FOLDER: str = Field(default=os.path.join(os.getcwd(), "uploads"))
    STORAGE_DIR: str = Field(default=os.path.join(os.getcwd(), "transcripts"))

    # --- Logging / Exports ---
    LOG_DIR: str = Field(default=os.path.join(os.getcwd(), "logs"))
    LOG_LEVEL: str = Field(default="INFO")
    EXPORT_DIR: str = Field(default=os.path.join(os.getcwd(), "exports"))

    # --- ASGI / Whisper Transcription ---
    asgi_enable_transcribe: bool = Field(default=False)
    asgi_load_model: bool = Field(default=False)
    whisper_model_size: str = Field(default="small")
    whisper_device: str = Field(default="cpu")      # cpu | cuda
    whisper_compute: str = Field(default="int8")    # int8 | float16 | float32

    # --- Config ---
    model_config = SettingsConfigDict(extra="ignore")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Backwards-compat export (many files do `from app.config import config`)
config: Settings = get_settings()

# IMPORTANT:
# Do NOT create network clients (Redis, DB) here.
# Anything that talks to the network must be created lazily elsewhere.
