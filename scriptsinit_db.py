#!/usr/bin/env python3
"""
Utility script to initialize the database schema.
Creates all tables defined in SQLAlchemy models.
"""
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import all models to ensure they are registered with Base
import app.models  # noqa: F401, E402
from app.db import Base, engine  # noqa: E402


def init_db():
    """
    Create all tables in the database based on SQLAlchemy models.
    """
    print(f"Initializing database schema on {engine.url}")
    Base.metadata.create_all(bind=engine)
    print("Database schema created successfully.")


if __name__ == "__main__":
    init_db()
