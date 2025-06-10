# Use a slim Python 3.11 base image
FROM python:3.11-slim

# Avoid Python writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC

# Set working directory
WORKDIR /app

# Install system-level dependencies required by WhisperX and audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install PyTorch CPU builds
RUN pip install --upgrade pip && \
    pip install torch==2.1.2 torchaudio==2.1.2 torchvision==0.16.2 \
    --extra-index-url https://download.pytorch.org/whl/cpu
# After: RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn[standard]


# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install WhisperX (no dependency reinstall to save time)
RUN pip install git+https://github.com/m-bain/whisperx.git@v3.2.0 --no-deps

# Copy project source code into container
COPY . .

# Start FastAPI server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

