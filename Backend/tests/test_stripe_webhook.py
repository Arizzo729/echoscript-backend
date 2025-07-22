# === tests/test_stripe_webhook.py ===
import json

import pytest
import stripe
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ensure models registered
from app.db import Base
from app.main import app
from tests.conftest import TestingSessionLocal


# By default, bypass Stripe signature verification for tests
@pytest.fixture(autouse=True)
def patch_stripe_construct_event(monkeypatch):
    """
    Monkeypatch stripe.Webhook.construct_event to return the parsed JSON payload
    for all tests, unless overridden in a specific test.
    """
    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        lambda payload, sig_header, secret: json.loads(payload),
    )


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Set up and tear down the DB for webhook tests.
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
async def test_webhook_invalid_signature(monkeypatch):
    """
    Simulate Stripe signature verification failure by raising
    SignatureVerificationError, expecting 400 response.
    """

    # Override construct_event to raise signature error
    def bad_construct(payload, sig_header, secret):
        raise stripe.error.SignatureVerificationError("Invalid signature", sig_header)

    monkeypatch.setattr(stripe.Webhook, "construct_event", bad_construct)

    payload = json.dumps({"type": "customer.subscription.created", "data": {}}).encode(
        "utf-8"
    )
    headers = {"Stripe-Signature": "t=123,v1=invalid"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", headers=headers
        ) as client:
            response = await client.post("/api/v1/stripe-webhook", content=payload)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_subscription_created():
    """
    When a customer.subscription.created event arrives,
    the endpoint should process it and return 200.
    """
    event = {
        "id": "evt_test123",
        "object": "event",
        "type": "customer.subscription.created",
        "data": {"object": {"id": "sub_test123", "customer": "cus_test456"}},
    }
    payload = json.dumps(event).encode("utf-8")
    headers = {"Stripe-Signature": "any"}  # signature check bypassed

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", headers=headers
        ) as client:
            response = await client.post("/api/v1/stripe-webhook", content=payload)

    assert response.status_code == 200
    # Optionally verify database state or side effects here


@pytest.mark.asyncio
async def test_webhook_unhandled_event_type():
    """
    When an unhandled event type arrives,
    the endpoint should acknowledge with 200 (no-op).
    """
    event = {"id": "evt_test999", "object": "event", "type": "ping", "data": {}}
    payload = json.dumps(event).encode("utf-8")
    headers = {"Stripe-Signature": "any"}

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", headers=headers
        ) as client:
            response = await client.post("/api/v1/stripe-webhook", content=payload)

    assert response.status_code == 200
