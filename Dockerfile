# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libglib2.0-0 \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir torch==2.2.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt




# Copy all remaining source files
COPY . .

# Expose the default FastAPI port
EXPOSE 8000

# Start the Uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

