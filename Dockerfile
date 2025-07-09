# ---- EchoScript.AI Dockerfile (CUDA + WhisperX-ready) ----
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    TORCH_HOME=/app/.torch_cache

# Install system deps
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python-is-python3 \
    ffmpeg git curl libsndfile1 libgl1 build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && python -m pip install torch==2.7.1+cu118 torchaudio==2.7.1 torchvision==0.22.1 \
      --extra-index-url https://download.pytorch.org/whl/cu118 \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create folders
RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

