# Dockerfile (backend)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (psycopg, lxml, ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libxml2-dev libxslt1-dev curl git ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Python deps (layered for cache)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r /app/requirements.txt

# App source
COPY . /app

# Railway injects $PORT; default to 8000 locally
ENV PORT=8000
EXPOSE 8000

# 👇 Linux shell (not Windows cmd)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]


