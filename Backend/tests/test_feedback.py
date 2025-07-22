import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ensure models are registered
from app.db import Base
from app.main import app
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down DB tables for feedback tests.
    """
    session = TestingSessionLocal()
    engine = session.bind
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session.close()

    yield

    session = TestingSessionLocal()
    engine = session.bind
    Base.metadata.drop_all(bind=engine)
    session.close()


@pytest.mark.asyncio
async def test_feedback_success():
    """
    Given valid feedback data,
    POST /api/v1/feedback should return 200 with acknowledgment.
    """
    payload = {
        "email": "user@example.com",
        "feedback": "This is a test feedback message.",
    }

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/feedback", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Feedback received"


@pytest.mark.asyncio
async def test_feedback_validation_error():
    """
    With missing fields,
    POST /api/v1/feedback should return 422 Unprocessable Entity.
    """
    # Missing 'feedback' field
    payload = {"email": "user@example.com"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/feedback", json=payload)

    assert response.status_code == 422
