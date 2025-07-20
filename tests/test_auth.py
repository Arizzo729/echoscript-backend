import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE_URL = "http://test"

@pytest.mark.asyncio
async def test_register_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        payload = {"email": "newuser@echoscript.ai", "password": "securepass"}
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 200
        assert "✅ Registration successful" in response.json()["message"]

@pytest.mark.asyncio
async def test_register_duplicate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        payload = {"email": "guest@echoscript.ai", "password": "guest"}
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered."

@pytest.mark.asyncio
async def test_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        payload = {"email": "guest@echoscript.ai", "password": "guest"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["user"]["email"] == "guest@echoscript.ai"

@pytest.mark.asyncio
async def test_login_invalid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        payload = {"email": "invalid@user.com", "password": "wrong"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."

@pytest.mark.asyncio
async def test_guest_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        response = await client.get("/auth/guest")
        assert response.status_code == 200
        json = response.json()
        assert json["user"]["email"] == "guest@echoscript.ai"
        assert "access_token" in json

@pytest.mark.asyncio
async def test_refresh_token():
    # First, get a token from /auth/guest
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        login = await client.get("/auth/guest")
        token = login.json()["access_token"]

        refresh = await client.post("/auth/refresh", json={"token": token})
        assert refresh.status_code == 200
        assert "access_token" in refresh.json()
