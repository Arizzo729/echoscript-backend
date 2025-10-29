#!/usr/bin/env python3
"""
Initialize the database schema by creating all tables defined in SQLAlchemy models.
Usage:
  python scripts/init_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import models so they register with Base.metadata
# (Your app.models should import/define all ORM models)
import app.models  # noqa: F401,E402
from app.db import Base, engine  # noqa: E402


def init_db() -> None:
    url = getattr(engine, "url", None)
    print(f"Initializing database schema on {url!s}")
    Base.metadata.create_all(bind=engine)
    print("✅ Database schema created successfully.")


if __name__ == "__main__":
    init_db()
