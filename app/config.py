from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "EchoScript API"
    API_PREFIX: str = "/api"

    # Accept either:
    # - JSON list: ["http://a","https://b"]
    # - CSV string: http://a,https://b
    CORS_ALLOW_ORIGINS: List[str] = []

    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                import json
                return json.loads(s)
            # CSV -> list
            return [u.strip() for u in s.split(",") if u.strip()]
        return v

    class Config:
        env_file = ".env"

settings = Settings()
# Back-compat for code that does: from app.config import config
config = settings