# app/db.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.settings import settings

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,
    connect_args=(
        {"check_same_thread": False}
        if settings.DATABASE_URL.startswith("sqlite")
        else {}
    ),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to provide a DB session per request.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()