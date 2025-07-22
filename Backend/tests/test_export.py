# === tests/test_export.py ===
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ensure models are registered
from app.db import Base
from app.main import app
from tests.conftest import TestingSessionLocal  # test DB session factory


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Set up and tear down the database tables for export tests.
    """
    session = TestingSessionLocal()
    engine = session.bind

    # Reset schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session.close()

    yield

    # Teardown after tests
    session = TestingSessionLocal()
    engine = session.bind
    Base.metadata.drop_all(bind=engine)
    session.close()


@pytest.mark.asyncio
async def test_export_transcript_success():
    """
    Given a valid transcript_id and export format,
    POST /api/v1/export should return 200 with export_id and status queued.
    """
    # TODO: seed a user, obtain JWT token, and create a transcript record matching transcript_id
    token = "test-jwt-token"
    payload = {"transcript_id": "existing-transcript-id", "format": "srt"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/export", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "export_id" in data
    assert data.get("status") == "queued"


@pytest.mark.asyncio
async def test_export_unauthorized():
    """
    Without an Authorization header,
    POST /api/v1/export should return 401 Unauthorized.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/export", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_validation_error():
    """
    With missing required fields,
    POST /api/v1/export should return 422 Unprocessable Entity.
    """
    token = "test-jwt-token"
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/export", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_export_status_success():
    """
    Given an existing export_id,
    GET /api/v1/export/{export_id} should return 200 with details including url or status.
    """
    # TODO: seed an export record in the DB or mock lookup
    export_id = "existing-export-id"
    token = "test-jwt-token"

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get(f"/api/v1/export/{export_id}")

    assert response.status_code == 200
    data = response.json()
    assert data.get("id") == export_id
    # Could include url or status
    assert "status" in data


@pytest.mark.asyncio
async def test_get_export_not_found():
    """
    With a non-existent export_id,
    GET /api/v1/export/{export_id} should return 404.
    """
    token = "test-jwt-token"
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/v1/export/not-real-id")

    assert response.status_code == 404
