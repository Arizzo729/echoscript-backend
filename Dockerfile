# Use official lightweight Python image
FROM python:3.13.5-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install OS-level dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libglib2.0-0 \
    git \
    curl \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Pre-copy requirements for caching
COPY requirements.txt .

# Install dependencies including stable, compatible Torch stack
RUN pip install --upgrade pip setuptools wheel \
 && pip install torch==2.5.1+cpu torchaudio==2.5.1+cpu torchvision==0.17.1+cpu --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose app port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


