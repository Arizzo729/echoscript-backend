# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (lxml + Postgres headers for psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libxml2-dev libxslt1-dev git \
 && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
# If you use requirements.txt, keep this block.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# (If you use Poetry instead of requirements.txt, remove the 2 lines above and use:)
# RUN pip install --no-cache-dir poetry \
#  && poetry config virtualenvs.create false
# COPY pyproject.toml poetry.lock* /app/
# RUN poetry install --no-root --no-interaction --no-ansi

# ---- App code ----
COPY . /app

# Ensure runtime dirs exist (optional/safe)
RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

# Default for local docker runs; Railway will inject PORT automatically
ENV PORT=8080

# Simple container healthcheck hitting /healthz
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python - <<'PY' || exit 1
import urllib.request, os, sys
try:
  url = f"http://127.0.0.1:{os.environ.get('PORT','8080')}/healthz"
  with urllib.request.urlopen(url, timeout=3) as r:
    sys.exit(0 if r.status==200 else 1)
except Exception:
  sys.exit(1)
PY

# IMPORTANT: bind to ${PORT} so Railway's proxy can reach the app
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

