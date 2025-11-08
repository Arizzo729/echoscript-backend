#!/usr/bin/env python3
"""
Add username column to users table.
Usage:
  python scripts/add_username_column.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text

def add_username_column() -> None:
    db_url = "sqlite:///./db.sqlite3"
    engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    print(f"Adding username column to users table in {db_url}")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR"))
            conn.commit()
            print("✅ Username column added successfully.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Username column already exists.")
            else:
                print(f"❌ Error adding username column: {e}")
                raise
        
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
            conn.commit()
            print("✅ Username index created successfully.")
        except Exception as e:
            print(f"ℹ️  Index creation skipped or already exists: {e}")

if __name__ == "__main__":
    add_username_column()
