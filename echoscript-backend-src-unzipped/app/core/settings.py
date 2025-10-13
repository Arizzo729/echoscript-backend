# app/core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """
    Centralized application settings using Pydantic.
    Reads from a .env file and environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core Application Settings ---
    APP_NAME: str = "EchoScript.AI"
    ENV: str = "development"
    DEBUG: bool = True
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    LOG_LEVEL: str = "DEBUG"
    # Comma-separated string of allowed origins
    API_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.API_ALLOWED_ORIGINS.split(",")]

    # --- JWT / Auth Settings ---
    SECRET_KEY: str = "your_super_secret_key_that_is_long_and_random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Database Settings ---
    DATABASE_URL: str = "sqlite:///./db.sqlite3"

    # --- Redis Settings ---
    REDIS_URL: str = "redis://localhost:6379/0"
    DISABLE_REDIS: bool = False

    # --- Email Settings (Resend or SMTP) ---
    # For Resend.com
    RESEND_API_KEY: str | None = None
    RESEND_FROM: str = "EchoScript <noreply@yourdomain.com>"
    # For SMTP
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    SMTP_FROM: str = "EchoScript <noreply@yourdomain.com>"
    # Default recipient for contact forms
    CONTACT_TO: str = "support@yourdomain.com"

    # --- Stripe Settings ---
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PUBLIC_KEY: str | None = None
    STRIPE_PRICE_PRO: str | None = None
    STRIPE_PRICE_PREMIUM: str | None = None
    STRIPE_SUCCESS_URL: str = "http://localhost:5173/purchase-success"
    STRIPE_CANCEL_URL: str = "http://localhost:5173/purchase"

    # --- PayPal Settings ---
    PAYPAL_ENV: str = "sandbox" # or "live"
    PAYPAL_CLIENT_ID: str | None = None
    PAYPAL_CLIENT_SECRET: str | None = None

    # --- AI / ML Model Settings ---
    OPENAI_API_KEY: str | None = None
    HUGGINGFACE_TOKEN: str | None = None
    # faster-whisper model size (e.g., "tiny", "base", "small", "medium", "large-v3")
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu" # "cuda" if you have a GPU
    WHISPER_COMPUTE: str = "int8" # "float16" for GPU
    PYANNOTE_PIPELINE: str = "pyannote/speaker-diarization-3.1"

    # --- File Paths (usually auto-detected, but can be overridden) ---
    UPLOAD_FOLDER: str = "c:\\AI collaberation\\EchoScriptAI\\echoscript-backend-src-unzipped\\app\\static\\uploads"
    STORAGE_DIR: str = "c:\\AI collaberation\\EchoScriptAI\\echoscript-backend-src-unzipped\\transcripts"
    EXPORT_DIR: str = "c:\\AI collaberation\\EchoScriptAI\\echoscript-backend-src-unzipped\\exports"
    LOG_DIR: str = "c:\\AI collaberation\\EchoScriptAI\\echoscript-backend-src-unzipped\\logs"


# Create a single, importable instance of the settings
settings = Settings()