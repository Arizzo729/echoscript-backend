#!/usr/bin/env python
"""Create test user in PostgreSQL"""
from app.db import SessionLocal
from app.models import User
from app.utils.auth_utils import hash_password

session = SessionLocal()

try:
    # Check if test user exists
    test_user = session.query(User).filter(User.email == 'test@gmail.com').first()
    
    if test_user:
        print(f"Test user exists: {test_user.email}")
        if test_user.hashed_password:
            print(f"✅ Has password")
        else:
            print(f"❌ No password - adding one")
            test_user.hashed_password = hash_password('Test@12345')
            session.commit()
            print("✅ Password added")
    else:
        print("Creating test user...")
        new_user = User(
            email='test@gmail.com',
            hashed_password=hash_password('Test@12345'),
            plan='free'
        )
        session.add(new_user)
        session.commit()
        print("✅ Test user created: test@gmail.com / Test@12345")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
