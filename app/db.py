# app/db.py
from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Neon/Postgres-friendly engine options
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    # Import models here so all tables are registered on Base before create_all
    from app.models import User, Subscription  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
