import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ✅ Import after app to avoid shadowing
from app.db import Base
from app.main import app  # ✅ Import FastAPI app first
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down DB tables for assistant tests.
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
async def test_assistant_success():
    """
    Given a valid prompt payload,
    POST /api/v1/assistant should return 200 with an AI response.
    """
    payload = {"prompt": "Hello, assistant!"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/assistant", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data


@pytest.mark.asyncio
async def test_assistant_validation_error():
    """
    Missing prompt field should yield 422.
    """
    payload = {}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/assistant", json=payload)

    assert response.status_code == 422
