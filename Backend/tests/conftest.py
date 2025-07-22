import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.dependencies import get_current_user, get_db
from app.main import app  # ✅ Import FastAPI app directly
from app.models import User

# Use an in-memory SQLite database for fast, isolated tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


# 1) Override the get_db dependency to yield this test session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Override dependencies using the FastAPI app instance
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
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
