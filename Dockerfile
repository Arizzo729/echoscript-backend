FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# ✅ Install Whisper stack FIRST (correct order)
RUN pip install --no-cache-dir \
    faster-whisper==1.0.3 \
    ctranslate2==4.5.0

# Copy requirements
COPY requirements.txt .

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "asgi_dev:app", "--host", "0.0.0.0", "--port", "8000"]
