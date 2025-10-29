# app/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "production"
    API_ALLOWED_ORIGINS: str
    JWT_SECRET: str
    STRIPE_SECRET_KEY: str
    STRIPE_PRICE_PRO: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    # add others here...

    class Config:
        env_file = ".env"  # local only; Railway uses real env

settings = Settings()  # raises if required vars missing
