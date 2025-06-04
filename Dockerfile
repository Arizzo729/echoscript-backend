# ---- EchoScript.AI: Dockerfile (CUDA + WhisperX-ready) ----

FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Environment settings
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    TORCH_HOME=/app/.torch_cache

# Install system dependencies + Python
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python-is-python3 \
    ffmpeg git curl libsndfile1 libgl1 build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Pre-install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create necessary folders
RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

# Expose API port
EXPOSE 8000

# Launch API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
