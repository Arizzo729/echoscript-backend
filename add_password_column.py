#!/usr/bin/env python
"""Add password column to PostgreSQL users table"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment from .env
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, inspect
import os

db_url = os.getenv("DATABASE_URL")
print(f"Database URL: {db_url[:50] if db_url else 'None'}...")

if not db_url:
    print("❌ DATABASE_URL not found in environment!")
    sys.exit(1)

try:
    engine = create_engine(db_url)
    
    # Check current columns
    inspector = inspect(engine)
    columns = {c['name']: c for c in inspector.get_columns('users')}
    print(f"Current columns: {list(columns.keys())}")
    
    if 'password' not in columns:
        print("\n❌ Password column missing! Adding it now...")
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN password VARCHAR(256)
            """))
            print("✅ Added password column to PostgreSQL")
    else:
        print("✅ Password column already exists")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
