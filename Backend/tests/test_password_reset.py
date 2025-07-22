import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app import models  # ensure User model is registered
from app.db import Base
from app.main import app
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Create and tear down the test database tables for the duration of this test module.
    """
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
async def test_send_reset_code_success():
    """
    When a user exists,
    POST /api/v1/send-reset-code should return 200.
    """
    # 1) Seed the database
    db = TestingSessionLocal()
    db.add(
        app.models.User(
            id=123, email="test@user.com", password="fakehashed", is_active=True
        )
    )
    db.commit()
    db.close()

    # 2) Call the endpoint
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/send-reset-code", json={"email": "test@user.com"}
            )
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_send_reset_code_user_not_found():
    """
    When no user exists,
    POST /api/v1/send-reset-code should return 404.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/send-reset-code", json={"email": "unknown@example.com"}
            )
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_reset_success():
    """
    When a valid reset code and new password are provided,
    POST /api/v1/verify-reset should return 200 and a new access token.
    """
    # TODO: seed or mock the reset code mechanism before calling verify-reset
    pass


@pytest.mark.asyncio
async def test_verify_reset_invalid_code():
    """
    When an invalid reset code is provided,
    POST /api/v1/verify-reset should return 400.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/verify-reset",
                json={
                    "email": "test@user.com",
                    "code": "wrong",
                    "new_password": "newpass",
                },
            )
            assert response.status_code == 400
