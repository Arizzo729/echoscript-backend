# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: lxml, Postgres headers, curl (for healthcheck), ffmpeg (optional but handy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libxml2-dev libxslt1-dev git curl ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r /app/requirements.txt

# ---- App code ----
COPY . /app

# Optional runtime dirs
RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

# Default for local; Railway injects PORT automatically
ENV PORT=8080

# Healthcheck hits the real FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null || exit 1

# IMPORTANT: bind to ${PORT} so Railway's proxy can reach the app
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

