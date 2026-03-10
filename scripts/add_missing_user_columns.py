#!/usr/bin/env python3
"""
Add missing columns to users table for PostgreSQL.
Usage:
  python scripts/add_missing_user_columns.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text

def add_missing_columns() -> None:
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:KBQZgJVeRSilmYiGSbsjNzJBBRUxmVlh@hopper.proxy.rlwy.net:58682/railway")
    engine = create_engine(db_url, future=True)
    print(f"Adding missing columns to users table in {db_url}")

    with engine.connect() as conn:
        # Add username column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100)"))
            conn.commit()
            print("✅ Username column added successfully.")
        except Exception as e:
            print(f"ℹ️  Username column: {e}")

        # Add is_active column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print("✅ is_active column added successfully.")
        except Exception as e:
            print(f"ℹ️  is_active column: {e}")

        # Add is_verified column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✅ is_verified column added successfully.")
        except Exception as e:
            print(f"ℹ️  is_verified column: {e}")

        # Add avatar_url column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR"))
            conn.commit()
            print("✅ avatar_url column added successfully.")
        except Exception as e:
            print(f"ℹ️  avatar_url column: {e}")

        # Add avatar_uploaded_at column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_uploaded_at TIMESTAMP"))
            conn.commit()
            print("✅ avatar_uploaded_at column added successfully.")
        except Exception as e:
            print(f"ℹ️  avatar_uploaded_at column: {e}")

        # Add updated_at column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"))
            conn.commit()
            print("✅ updated_at column added successfully.")
        except Exception as e:
            print(f"ℹ️  updated_at column: {e}")

        # Create indexes
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
            conn.commit()
            print("✅ Username index created successfully.")
        except Exception as e:
            print(f"ℹ️  Username index: {e}")

if __name__ == "__main__":
    add_missing_columns()