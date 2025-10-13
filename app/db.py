# app/db.py
from collections.abc import Generator

# pydantic and pydantic-settings have changed exports between versions.
# Try the newer pydantic-settings package first, then fall back to pydantic's types
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
except Exception:  # pragma: no cover - runtime compatibility
    try:
        # pydantic v2 exposes ConfigDict; alias it for compatibility
        from pydantic import BaseSettings, ConfigDict as SettingsConfigDict  # type: ignore
    except Exception:
        # Last-resort fallback: provide minimal stand-ins so imports succeed in tests
        from pydantic import BaseSettings  # type: ignore

        class SettingsConfigDict(dict):
            """Fallback placeholder for SettingsConfigDict when running with older/unknown pydantic.

            It behaves like a plain dict which is sufficient for simple model_config usage in this codebase.
            """
            pass
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
