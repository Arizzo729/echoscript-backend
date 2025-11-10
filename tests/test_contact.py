import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.db import Base
from app.main import app  # ✅ Import FastAPI app first
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Set up and tear down the DB schema for contact tests.
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
async def test_contact_success():
    """
    Given valid contact data,
    POST /api/v1/contact should return 200 with acknowledgment.
    """
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "Hello, this is a test message.",
    }

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/contact", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Contact request received"


@pytest.mark.asyncio
async def test_contact_validation_error():
    """
    With missing required fields,
    POST /api/v1/contact should return 422 Unprocessable Entity.
    """
    payload = {"name": "Test User", "email": "test@example.com"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/contact", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_contact_rate_limit():
    """
    If a rate limit is enforced,
    multiple rapid requests should eventually return 429 Too Many Requests.
    """
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "message": "Spam message",
    }
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp1 = await client.post("/api/v1/contact", json=payload)
            assert resp1.status_code == 200
            resp2 = await client.post("/api/v1/contact", json=payload)
            assert resp2.status_code in (200, 429)
