# === tests/test_subscription.py ===
import pytest
from datetime import datetime

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from app.main import app
from app.db import Base
import app.models  # ensure User and Subscription models are registered

from app.models import Subscription, SubscriptionStatus
from tests.conftest import TestingSessionLocal  # our test DB session factory

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down the test database tables for the duration of this test module.
    """
    # Initialize a session to access the engine
    session = TestingSessionLocal()
    engine = session.bind

    # Ensure a clean slate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session.close()
    yield

    # Tear down
    session = TestingSessionLocal()
    engine = session.bind
    Base.metadata.drop_all(bind=engine)
    session.close()

@pytest.mark.asyncio
async def test_get_my_subscription_none():
    """
    When no subscription exists for user 123,
    GET /api/subscription/me should return 404.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/subscription/me")
            assert response.status_code == 404
            assert response.json()["detail"] == "No active subscription found for this user."

@pytest.mark.asyncio
async def test_get_my_subscription_active():
    """
    Insert a Subscription for user 123 using the test session,
    then GET /api/subscription/me should return it.
    """
    # 1) Seed the database
    db = TestingSessionLocal()
    db.add(Subscription(
        user_id=123,
        stripe_subscription_id="sub_123",
        stripe_customer_id="cus_456",
        plan_name="Pro",
        status=SubscriptionStatus.active,
        started_at=datetime.utcnow()
    ))
    db.commit()
    db.close()

    # 2) Now call the endpoint
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/subscription/me")
            assert response.status_code == 200

            data = response.json()
            assert data["stripe_subscription_id"] == "sub_123"
            assert data["stripe_customer_id"] == "cus_456"
            assert data["plan_name"] == "Pro"
            assert data["status"] == "active"


