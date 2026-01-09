FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    ffmpeg \
    git \
    curl \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

# Make python point to python3.10
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install Whisper stack FIRST (critical)
RUN pip install --no-cache-dir \
    ctranslate2==4.4.0 \
    faster-whisper==1.0.3

# Install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "asgi_dev:app", "--host", "0.0.0.0", "--port", "8000"]
