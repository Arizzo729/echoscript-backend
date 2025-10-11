import os
from functools import lru_cache
from typing import Optional

try:
    # Pydantic v2
    from pydantic import BaseSettings, Field
except Exception:  # pragma: no cover
    # Fallback to v1 if your env is older
    from pydantic import BaseSettings  # type: ignore
    Field = lambda default=None, **_: default  # type: ignore


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
    # For local dev: set REDIS_ENABLED=false OR leave REDIS_URL blank.
    REDIS_ENABLED: bool = Field(default=True)
    REDIS_URL: Optional[str] = None  # e.g. redis://:password@host:port/0

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

