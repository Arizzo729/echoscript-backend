import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ✅ Register models after app is defined
from app.db import Base
from app.main import app  # ✅ Import FastAPI app before anything named "app"
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down the test database tables for this module.
    """
    session = TestingSessionLocal()
    engine = session.bind

    # Clean slate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session.close()

    yield

    # Teardown
    session = TestingSessionLocal()
    engine = session.bind
    Base.metadata.drop_all(bind=engine)
    session.close()


@pytest.mark.asyncio
async def test_transcribe_success():
    """
    Given a valid audio URL and authorization,
    POST /api/v1/transcribe should return 200 with transcription details.
    """
    # TODO: seed a user and obtain a valid JWT token before calling
    token = "test-jwt-token"
    payload = {"audio_url": "http://example.com/audio.mp3"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/transcribe", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "transcript_id" in data
    assert data.get("status") == "queued"


@pytest.mark.asyncio
async def test_transcribe_unauthorized():
    """
    Without an Authorization header,
    POST /api/v1/transcribe should return 401 Unauthorized.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/transcribe", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_transcribe_validation_error():
    """
    With missing required fields,
    POST /api/v1/transcribe should return 422 Unprocessable Entity.
    """
    token = "test-jwt-token"
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            # Empty payload triggers pydantic validation error
            response = await client.post("/api/v1/transcribe", json={})

    assert response.status_code == 422
