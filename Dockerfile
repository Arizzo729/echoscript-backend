# Use Python 3.11 slim base image for smaller size & latest features
FROM python:3.11-slim

# Environment for better Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC

WORKDIR /app

# Install system deps needed for audio and WhisperX
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 git curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only with audio libs
RUN pip install --upgrade pip && \
    pip install torch==2.1.2 torchaudio==2.1.2 torchvision==0.16.2 \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install Uvicorn early for entrypoint sanity
RUN pip install uvicorn[standard]

# Copy and install your requirements (faster caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install WhisperX pinned stable release without extras to avoid conflicts
RUN pip install git+https://github.com/m-bain/whisperx.git@v3.2.0 --no-deps

# Copy entire project source
COPY . .

# Entrypoint: launch FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



