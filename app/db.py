# === app/db.py — Database Engine & Session ===

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import config  # ← use the instantiated Config object, not class

# === Dynamic DB URL ===
DATABASE_URL = config.DATABASE_URL

# === Engine Setup ===
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

# === Session Factory ===
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False  # Optional: avoids lazy-loading bugs after commit
)

# === Declarative Base ===
Base = declarative_base()

# === FastAPI Dependency Injection ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
