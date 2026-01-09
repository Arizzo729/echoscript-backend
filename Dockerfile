FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    build-essential \
    ffmpeg \
    git \
    curl \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

# Use python3.10 explicitly
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install Whisper stack FIRST (CRITICAL)
RUN pip install --no-cache-dir \
    ctranslate2==4.4.0 \
    faster-whisper==1.0.3

# Install rest of your deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "asgi_dev:app", "--host", "0.0.0.0", "--port", "8000"]
