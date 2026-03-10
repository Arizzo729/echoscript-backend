#!/usr/bin/env python
"""
Check database state and create users table properly
"""
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Session, sessionmaker
import sys

# Get database URL from environment
db_url = os.getenv("DATABASE_URL")
print(f"Using database: {db_url[:50] if db_url else 'DEFAULT'}...")

# Create engine
try:
    if db_url:
        engine = create_engine(db_url)
    else:
        engine = create_engine("sqlite:///./db.sqlite3")
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    
    # Get existing tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
    
    if 'users' in tables:
        columns = {c['name']: c for c in inspector.get_columns('users')}
        print(f"Users table columns: {list(columns.keys())}")
        
        if 'password' not in columns:
            print("\n❌ Password column is MISSING! Adding it now...")
            with engine.begin() as conn:
                conn.execute(text("""
                    ALTER TABLE users ADD COLUMN password VARCHAR(256)
                """))
                print("✅ Added password column")
        else:
            print("✅ Password column exists")
    else:
        print("❌ Users table doesn't exist!")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
