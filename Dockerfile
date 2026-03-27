FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
 PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
 build-essential gcc libpq-dev libxml2-dev libxslt1-dev curl git ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r /app/requirements.txt

COPY . /app

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=12 \
 CMD curl -fsS "http://127.0.0.1:${PORT}/api/healthz" || exit 1

# RunPod production entrypoint: use canonical app router setup.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
