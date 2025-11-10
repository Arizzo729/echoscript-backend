# Thin compatibility wrapper expected by tests: expose the FastAPI `app` at module top-level
from app.main import app  # re-export

__all__ = ["app"]
