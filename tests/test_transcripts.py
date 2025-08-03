import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import \
    models  # ✅ Keep this *after* FastAPI app import to avoid shadowing
from app.db import Base
from app.main import app  # ✅ Only this app import allowed
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down DB tables for transcripts tests.
    """
    session = TestingSessionLocal()
    engine = session.bind

    # Reset schema
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
async def test_list_transcripts_success():
    token = "test-jwt-token"

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/v1/transcripts")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert "id" in first
        assert "created_at" in first


@pytest.mark.asyncio
async def test_get_transcript_success():
    transcript_id = "existing-transcript-id"
    token = "test-jwt-token"

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get(f"/api/v1/transcripts/{transcript_id}")

    assert response.status_code == 200
    data = response.json()
    assert data.get("id") == transcript_id
    assert "text" in data


@pytest.mark.asyncio
async def test_get_transcript_not_found():
    token = "test-jwt-token"
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/v1/transcripts/not-real-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_transcripts_unauthorized():
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/transcripts")

    assert response.status_code == 401
