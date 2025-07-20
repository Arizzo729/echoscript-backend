# 6. tests/conftest.py (corrected)

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.dependencies import get_db, get_current_user
import app.models                # register all ORM models on Base.metadata
from app.models import User
from app.main import app

# Use an in-memory SQLite database for fast, isolated tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {},
    future=True,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    future=True,
)

# 1) Override the get_db dependency to yield this test session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 2) Stub the current_user dependency to always return a fixed test user
def override_get_current_user():
    return User(id=123, email="test@user.com", password="fakehashed", is_active=True)

app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """
    Create all tables before tests run, then drop them afterwards.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

