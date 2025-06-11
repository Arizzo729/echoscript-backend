# Use Python 3.11 slim base image
FROM python:3.11-slim

# Avoid .pyc files and ensure real-time logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC

WORKDIR /app

# Install system dependencies needed by WhisperX, Torch, and audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install torch & audio libs with official CPU-only versions
RUN pip install --upgrade pip && \
    pip install torch==2.1.2 torchaudio==2.1.2 torchvision==0.16.2 \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install Uvicorn manually for early entrypoint testing
RUN pip install uvicorn[standard]

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install whisperx pinned from GitHub, no extra deps
RUN pip install git+https://github.com/m-bain/whisperx.git@v3.2.0 --no-deps

# Copy source code
COPY . .

# Launch server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


