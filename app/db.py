import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()

# Database URL configuration: default to SQLite for local dev, override via env in production
database_url = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

# Create SQLAlchemy engine
engine = create_engine(
    database_url,
    future=True,  # Use SQLAlchemy 2.0 style
    echo=False,  # Disable SQL echoing; set True for debugging
    pool_pre_ping=True,  # Test connections for stale connections
    connect_args=(
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    ),
)

# Session factory for creating new sessions
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base class for ORM models\ nBase = declarative_base()


# Dependency for FastAPI routes
def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session, ensuring it is closed after use.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Convenience global session (e.g., for scripts)
db_session: Session = SessionLocal()

# Explicit exports for convenience
__all__ = [
    "engine",
    "SessionLocal",
    "Session",
    "db_session",
    "get_db",
    "Base",
]
