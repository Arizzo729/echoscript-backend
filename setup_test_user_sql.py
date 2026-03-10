#!/usr/bin/env python
"""Set up test user directly using SQL"""
import os
from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL")

if not db_url:
    # Try loading from .env
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

print(f"Connecting to: {db_url[:50]}...")

engine = create_engine(db_url)

try:
    with engine.begin() as conn:
        # Check if test user exists
        result = conn.execute(text("""
            SELECT id, email, password FROM users WHERE email = 'test@gmail.com'
        """))
        user = result.fetchone()
        
        if user:
            user_id, email, pwd = user
            print(f"Test user exists: {email}")
            if pwd:
                print(f"✅ Has password")
            else:
                print(f"❌ No password - adding one")
                from app.utils.auth_utils import hash_password
                hashed = hash_password('Test@12345')
                conn.execute(text("""
                    UPDATE users SET password = :pwd WHERE email = 'test@gmail.com'
                """), {"pwd": hashed})
                print("✅ Password added")
        else:
            print("Creating test user...")
            from app.utils.auth_utils import hash_password
            hashed = hash_password('Test@12345')
            conn.execute(text("""
                INSERT INTO users (email, password, username, is_active, created_at)
                VALUES (:email, :pwd, :username, true, NOW())
            """), {"email": "test@gmail.com", "pwd": hashed, "username": "testuser"})
            print("✅ Test user created: test@gmail.com / Test@12345")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
