# tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.models import User
from app.utils.auth_utils import hash_password

# Use an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the database tables before any tests run, and drop them afterward
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Override the get_db dependency to use our testing database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_login_and_refresh_token():
    # Insert a test user directly into the database
    db = TestingSessionLocal()
    test_user = User(
        email="test@example.com", password=hash_password("password123"), is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    db.close()

    # 1. Test successful login
    login_resp = client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    token = login_data["access_token"]

    # 2. Test token refresh
    refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": token})
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.json()
    assert "access_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"
