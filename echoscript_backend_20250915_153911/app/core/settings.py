# app/core/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load .env and ignore any extra keys so startup never fails
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # (Optional) Common fields you actually use elsewhere in code.
    # If any of these aren't in your .env, the defaults below are used.
    env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str | None = None
    allow_origins: str | None = None

    # Auth / JWT
    secret_key: str | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"

    # Stripe
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_public_key: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_premium: str | None = None

    # ASR / ML
    asr_model: str | None = None
    whisper_model_size: str | None = None
    whisper_device: str | None = None
    whisper_compute: str | None = None
    huggingface_token: str | None = None
    pyannote_pipeline: str | None = None
    openai_api_key: str | None = None

    # Email / misc
    from_email: str | None = None
    vite_api_base: str | None = None
    smtp_key: str | None = None


settings = Settings()
