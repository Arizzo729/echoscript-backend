#!/usr/bin/env python
"""
Add password column to PostgreSQL users table
Run this from the backend directory: python -m fix_password_column
"""
import os
import sys

# Load environment
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    # Import after path is set
    from app.db import engine
    from sqlalchemy import text, inspect
    
    print("Checking database schema...")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'users' not in tables:
            print("❌ ERROR: users table doesn't exist")
            return False
        
        columns = {c['name']: c for c in inspector.get_columns('users')}
        print(f"Found {len(columns)} columns in users table")
        
        if 'password' in columns:
            print("✅ Password column already exists in users table")
            return True
        
        print("⚠️  Password column missing! Adding it...")
        
        with engine.begin() as conn:
            # Add the password column as nullable first
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN password VARCHAR(256)
            """))
            
            print("✅ Successfully added password column to users table")
            print("⚠️  Existing users have NULL passwords - they need to use 'Forgot Password' link")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
