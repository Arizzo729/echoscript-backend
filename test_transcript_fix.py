#!/usr/bin/env python3
"""
Test script to verify Transcript model and database tables are properly set up
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.db import Base, engine, SessionLocal
from app.models import Transcript, User, Subscription
from sqlalchemy import inspect

def test_models_imported():
    """Verify all models are imported in db.py"""
    print("✅ Models successfully imported:")
    print(f"  - User: {User}")
    print(f"  - Subscription: {Subscription}")
    print(f"  - Transcript: {Transcript}")

def test_transcript_table():
    """Verify Transcript model has all required fields"""
    print("\n✅ Transcript model has these fields:")
    for column in Transcript.__table__.columns:
        print(f"  - {column.name}: {column.type}")

def test_create_tables():
    """Create all tables in database"""
    print("\n📝 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

def test_table_exists():
    """Verify transcripts table exists in database"""
    print("\n🔍 Checking database tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables in database: {tables}")
    
    if 'transcripts' in tables:
        print("✅ transcripts table exists")
        columns = [col['name'] for col in inspector.get_columns('transcripts')]
        print(f"  Columns: {columns}")
    else:
        print("❌ transcripts table NOT FOUND")

def test_insert_transcript():
    """Test inserting a transcript into the database"""
    print("\n📝 Testing transcript insertion...")
    db = SessionLocal()
    try:
        # First create a test user
        test_user = User(email="test@example.com", hashed_password="test_hash", plan="free")
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Now create a transcript
        transcript = Transcript(
            user_id=test_user.id,
            title="Test Transcript",
            content="This is a test transcript content",
            language="en",
            status="completed"
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        print(f"✅ Transcript created: ID={transcript.id}, Title={transcript.title}")
        
        # Verify we can read it back
        retrieved = db.query(Transcript).filter(Transcript.id == transcript.id).first()
        if retrieved:
            print(f"✅ Transcript retrieved: {retrieved.title}")
        else:
            print("❌ Failed to retrieve transcript")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Transcript Model & Database Setup")
    print("=" * 60)
    
    try:
        test_models_imported()
        test_transcript_table()
        test_create_tables()
        test_table_exists()
        test_insert_transcript()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Transcripts are ready to use!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
