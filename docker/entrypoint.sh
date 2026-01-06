#!/bin/sh
set -e
exec python -m uvicorn asgi_dev:app --host 0.0.0.0 --port "${PORT:-8000}"




