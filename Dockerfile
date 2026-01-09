FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CTRANSLATE2_CUDA_ARCH_LIST="" \
    CTRANSLATE2_USE_MKL=0

WORKDIR /app

# System dependencies required to BUILD ctranslate2 safely
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    ffmpeg \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip & tools
RUN python -m pip install --upgrade pip setuptools wheel

# ⛔ IMPORTANT: install ctranslate2 FROM SOURCE (no prebuilt wheels)
RUN pip install --no-binary=ctranslate2 ctranslate2

# Install faster-whisper AFTER ctranslate2
RUN pip install faster-whisper

# Install remaining dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=12 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/healthz" || exit 1

CMD ["uvicorn", "asgi_dev:app", "--host", "0.0.0.0", "--port", "8000"]
