import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.db import Base
from app.main import app
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Set up and tear down the DB schema for newsletter tests.
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
async def test_subscribe_newsletter_success():
    """
    Given a valid email,
    POST /api/v1/newsletter should return 200 with confirmation.
    """
    payload = {"email": "test@example.com"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/newsletter", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Subscribed successfully"


@pytest.mark.asyncio
async def test_subscribe_newsletter_validation_error():
    """
    With missing email field,
    POST /api/v1/newsletter should return 422 Unprocessable Entity.
    """
    payload = {}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/newsletter", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_subscription_handled():
    """
    When subscribing the same email twice,
    the second POST should return 400 or idempotent success.
    """
    payload = {"email": "test@example.com"}
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp1 = await client.post("/api/v1/newsletter", json=payload)
            assert resp1.status_code == 200
            resp2 = await client.post("/api/v1/newsletter", json=payload)
            assert resp2.status_code in (200, 400)
