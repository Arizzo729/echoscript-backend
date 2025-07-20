# === app/db.py ===

import os

# -----------------------------------------------------------------------------
# Core SQLAlchemy imports (every commonly-used construct)
# -----------------------------------------------------------------------------
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    Text,
    JSON,
    Enum,
    ForeignKey,
    Index,
    UniqueConstraint,
    Sequence,
    Table,
    MetaData,
    func,
    select,
    text,
    event,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    backref,
    sessionmaker,
    Session,
    scoped_session,
    joinedload,
    subqueryload,
    selectinload,
    aliased,
)
from sqlalchemy.pool import Pool

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

# -----------------------------------------------------------------------------
# Engine & Session Factory
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    future=True,             # Use SQLAlchemy 2.0 style
    echo=False,              # Toggle SQL logging
    pool_pre_ping=True,      # Health-check pooled connections
    connect_args={"check_same_thread": False}
        if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    future=True,
)

# -----------------------------------------------------------------------------
# Declarative Base
# -----------------------------------------------------------------------------
Base = declarative_base()

# -----------------------------------------------------------------------------
# FastAPI Dependency
# -----------------------------------------------------------------------------
def get_db() -> Session:
    """
    FastAPI dependency that yields a transactional session
    and ensures it’s closed after use.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# Global Session (for scripts/utilities)
# -----------------------------------------------------------------------------
db_session: Session = SessionLocal()

# -----------------------------------------------------------------------------
# Explicit exports
# -----------------------------------------------------------------------------
__all__ = [
    # Config & core
    "os", "DATABASE_URL",
    # Engine & sessions
    "engine", "SessionLocal", "Session", "db_session", "get_db",
    # Declarative base
    "declarative_base", "Base",
    # SQLAlchemy core constructs
    "create_engine", "Column", "Integer", "String", "Boolean", "DateTime",
    "Float", "Text", "JSON", "Enum", "ForeignKey", "Index", "UniqueConstraint",
    "Sequence", "Table", "MetaData", "func", "select", "text", "event",
    # ORM utilities
    "relationship", "backref", "scoped_session",
    "joinedload", "subqueryload", "selectinload", "aliased",
    # Connection pooling
    "Pool",
]
