# === EchoScript.AI Dockerfile (corrected) ===
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    TORCH_HOME=/app/.torch_cache

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python-is-python3 \
    ffmpeg git curl libsndfile1 libgl1 build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m pip install --upgrade pip \
 && python3 -m pip install torch==2.7.1+cu118 torchaudio==2.7.1+cu118 torchvision==0.22.1+cu118 \
      --extra-index-url https://download.pytorch.org/whl/cu118 \
 && python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


