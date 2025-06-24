# Use official lightweight Python image
FROM python:3.11-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install OS-level deps (incl. FFmpeg, libsndfile, build tools for PyAV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libglib2.0-0 \
    git \
    curl \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libavfilter-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python deps: Uvicorn, Torch stack, then the rest
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir uvicorn[standard] \
 && pip install --no-cache-dir \
      torch==2.7.1+cu128 \
      torchaudio==2.7.1 \
      torchvision==0.22.1 \
    -f https://download.pytorch.org/whl/torch/ \
 && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port and run Uvicorn with 4 workers
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
