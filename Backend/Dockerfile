```dockerfile
# EchoScript.AI Backend Dockerfile
# Base image with CUDA support for WhisperX GPU inference
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    TORCH_HOME=/app/.torch_cache

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev python-is-python3 \
        ffmpeg git curl libsndfile1 build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary runtime directories
RUN mkdir -p \
        /app/transcripts \
        /app/static/uploads \
        /app/exports \
        /app/logs

# Create non-root user and set permissions
RUN groupadd -r echouser && \
    useradd -r -g echouser echouser && \
    chown -R echouser:echouser /app
USER echouser

# Expose application port
EXPOSE 8000

# Launch the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
