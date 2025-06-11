# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import Config

# ---- Dynamic DB Config ----
DATABASE_URL = Config.DATABASE_URL

# ---- Engine Setup ----
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ---- Dependency for FastAPI routes ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
