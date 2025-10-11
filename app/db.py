# app/db.py
from collections.abc import Generator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    DATABASE_URL: str = "sqlite:///./db.sqlite3"

settings = Settings()

Base = declarative_base()

# Use the DATABASE_URL from environment (fallback to SQLite). Strip any prefix if present.
url = settings.DATABASE_URL
if url.startswith("DATABASE_URL="):
    url = url.split("DATABASE_URL=", 1)[1]

engine = create_engine(
    url,
    future=True,
    echo=False,
    pool_pre_ping=True,
    connect_args=(
        {"check_same_thread": False}
        if url.startswith("sqlite")
        else {}
    ),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_session: Session = SessionLocal()
