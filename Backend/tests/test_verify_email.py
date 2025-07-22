# === tests/test_verify_email.py ===
import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.db import Base
from app.main import app
from app.models import User
from tests.conftest import TestingSessionLocal


# Fixture to seed a pending-verification user
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # ensure clean state
    engine = TestingSessionLocal().bind
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # seed a user with a known token
    db = TestingSessionLocal()
    user = User(email="verify@user.com", password="irrelevant", is_active=False)
    db.add(user)
    db.commit()
    # imagine you store a token somewhere; for this stub we'll hard-code:
    global VALID_TOKEN
    VALID_TOKEN = "valid-token-123"
    # In reality, you'd insert it into your verification table or encode it in JWT
    db.close()

    yield

    # teardown
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_verify_email_with_valid_token():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/auth/verify-email?token={VALID_TOKEN}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Email verified successfully"


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/auth/verify-email?token=bad-token")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid or expired verification token"


@pytest.mark.asyncio
async def test_verify_email_already_verified():
    # calling twice should fail
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # first call (valid)
        await client.get(f"/api/auth/verify-email?token={VALID_TOKEN}")
        # second call
        response = await client.get(f"/api/auth/verify-email?token={VALID_TOKEN}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already verified"
