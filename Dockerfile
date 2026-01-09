FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ===============================
# System dependencies (BUILD)
# ===============================
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

# ===============================
# Python build tools
# ===============================
RUN python -m pip install --upgrade pip setuptools wheel

# ===============================
# 🔥 BUILD CTRANSLATE2 FROM SOURCE (NO WHEELS)
# ===============================
RUN pip install \
    git+https://github.com/OpenNMT/CTranslate2.git@v4.4.0

# ===============================
# Install faster-whisper AFTER ctranslate2
# ===============================
RUN pip install faster-whisper

# ===============================
# Other app dependencies
# ===============================
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ===============================
# App code
# ===============================
COPY . /app

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=12 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/healthz" || exit 1

CMD ["uvicorn", "asgi_dev:app", "--host", "0.0.0.0", "--port", "8000"]
