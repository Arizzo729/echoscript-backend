from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_boot():
    # If your health path is "/", change it here.
    r = c.get("/healthz")
    assert r.status_code in (200, 204)
