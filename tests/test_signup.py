# tests/test_signup.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from main import app

# Use an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the database tables before tests run, and drop them afterward
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


@pytest.fixture(autouse=True)
def disable_email(monkeypatch):
    # Prevent actual emails being sent during signup
    import app.routes.signup as signup_module

    monkeypatch.setattr(signup_module, "send_email", lambda *args, **kwargs: None)


def test_successful_signup():
    response = client.post(
        "/api/auth/signup",
        json={"email": "newuser@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "sent"}


def test_duplicate_signup():
    # First signup
    client.post(
        "/api/auth/signup",
        json={"email": "dupuser@example.com", "password": "Password1"},
    )
    # Attempt duplicate signup
    response = client.post(
        "/api/auth/signup",
        json={"email": "dupuser@example.com", "password": "Password1"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"
