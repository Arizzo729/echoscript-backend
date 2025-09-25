# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    TORCH_HOME=/app/.torch_cache \
    PORT=10000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip wheel setuptools && \
    python -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /app/requirements.txt

COPY . /app
RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

EXPOSE 10000

CMD ["bash","-lc","python - <<'PY'\nimport os;from uvicorn import run\nport=int(os.environ.get('PORT','10000'))\nrun('app.main:app',host='0.0.0.0',port=port)\nPY"]
