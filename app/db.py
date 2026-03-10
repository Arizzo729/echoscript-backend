# app/db.py
import os
from collections.abc import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# CRITICAL: Load .env BEFORE reading environment variables
load_dotenv(".env")

# Import models here so SQLAlchemy knows about them
from app.models import User, Subscription, Transcript  # Make sure all models are imported

Base = declarative_base()

# Load DATABASE_URL from environment (or fallback to SQLite for development)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL connection
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        pool_pre_ping=True,  # Test connections before using them
    )
else:
    # SQLite connection
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        connect_args={"check_same_thread": False},  # SQLite specific
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_session: Session = SessionLocal()

# Automatically create tables
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

# Run table creation if executed directly
if __name__ == "__main__":
    init_db()

# app/db.py (add at the bottom)
from app.models import User, Subscription, Transcript  # make sure all models are imported

def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
