import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ✅ Register models after app is defined
from app.db import Base
from app.main import \
    app  # ✅ Define app before anything else that might define "app"
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down DB tables for subscription tests.
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
async def test_create_subscription_success():
    """
    Given a valid plan_id and auth,
    POST /api/v1/subscription should return 200 with subscription_id and active status.
    """
    # TODO: seed a user and available plan in DB
    token = "test-jwt-token"
    payload = {"plan_id": "basic"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/subscription", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "subscription_id" in data
    assert data.get("status") == "active"


@pytest.mark.asyncio
async def test_create_subscription_unauthorized():
    """
    Without auth header,
    POST /api/v1/subscription should return 401.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/subscription", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_subscription_validation_error():
    """
    With missing plan_id,
    POST /api/v1/subscription should return 422.
    """
    token = "test-jwt-token"
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post("/api/v1/subscription", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_subscription_success():
    """
    Given an active subscription,
    GET /api/v1/subscription should return 200 with subscription details.
    """
    # TODO: seed a subscription record for the test user
    token = "test-jwt-token"

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/v1/subscription")

    assert response.status_code == 200
    data = response.json()
    assert data.get("plan_id") == "basic"
    assert data.get("status") == "active"


@pytest.mark.asyncio
async def test_cancel_subscription_success():
    """
    Given an existing subscription,
    DELETE /api/v1/subscription should return 200 and confirmation of cancellation.
    """
    token = "test-jwt-token"

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.delete("/api/v1/subscription")

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "canceled"
