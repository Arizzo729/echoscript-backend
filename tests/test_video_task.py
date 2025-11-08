import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.db import Base
from app.main import app  # ✅ correct import
from tests.conftest import TestingSessionLocal  # test DB session factory


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Initialize and tear down the test database for video task tests.
    """
    session = TestingSessionLocal()
    engine = session.bind

    # Create fresh tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session.close()

    yield

    # Drop tables after tests
    session = TestingSessionLocal()
    engine = session.bind
    Base.metadata.drop_all(bind=engine)
    session.close()


@pytest.mark.asyncio
async def test_create_video_task_success():
    """
    Given a valid video URL and authorization,
    POST /api/v1/video-task should return 200 with task details.
    """
    token = "test-jwt-token"
    payload = {"video_url": "http://example.com/video.mp4"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/video-task", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data.get("status") == "queued"


@pytest.mark.asyncio
async def test_create_video_task_unauthorized():
    """
    Without Authorization header,
    POST /api/v1/video-task should return 401 Unauthorized.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/video-task", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_video_task_validation_error():
    """
    With missing video_url field,
    POST /api/v1/video-task should return 422 Unprocessable Entity.
    """
    token = "test-jwt-token"
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/video-task", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_video_task_status():
    """
    Given an existing task_id,
    GET /api/v1/video-task/{task_id}/status should return 200 with status field.
    """
    task_id = "existing-task-id"

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/video-task/{task_id}/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
