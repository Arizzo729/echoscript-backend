from typing import List
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "EchoScript API"
    API_PREFIX: str = "/api"
    CORS_ALLOW_ORIGINS: List[AnyHttpUrl] = []

    # Optional DB/Redis/Auth fields to avoid AttributeErrors if imported
    DATABASE_URL: str | None = None
    REDIS_URL: str | None = None
    JWT_SECRET: str | None = None
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()

# Backwards-compat for code that does: from app.config import config
config = settings