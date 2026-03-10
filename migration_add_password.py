#!/usr/bin/env python
"""
Migration script to add password column to users table in PostgreSQL if missing
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, inspect
from app.db import engine

def migrate():
    """Add password column to users table if it doesn't exist"""
    
    # Print connection info
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
    print(f"Engine: {engine}")
    
    try:
        # Check if users table exists and what columns it has
        inspector = inspect(engine)
        
        if 'users' not in inspector.get_table_names():
            print("❌ Users table doesn't exist!")
            return False
        
        existing_columns = [c['name'] for c in inspector.get_columns('users')]
        print(f"Existing columns: {existing_columns}")
        
        if 'password' in existing_columns:
            print("✅ Password column already exists")
            return True
        
        # Add password column
        print("Adding password column to users table...")
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN password VARCHAR(256)
            """))
            print("✅ Successfully added password column")
            
            # Update existing users with a placeholder (they need to reset password)
            conn.execute(text("""
                UPDATE users SET password = 'PLACEHOLDER_NEEDS_RESET' WHERE password IS NULL
            """))
            print("⚠️  Existing users need to use 'Forgot Password' to set a password")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
