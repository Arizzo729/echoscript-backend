# Minimal shim of asgi_lifespan.LifespanManager used in tests
# The real package runs the ASGI lifespan protocol; tests here only need a
# context manager/async context manager that starts and stops the app.

from contextlib import asynccontextmanager
from types import SimpleNamespace


@asynccontextmanager
async def LifespanManager(app):
    # No real startup/shutdown; yield control so tests can use the ASGI app.
    yield SimpleNamespace(app=app)
