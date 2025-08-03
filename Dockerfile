FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache \
    TORCH_HOME=/app/.torch_cache

WORKDIR /app

# === System dependencies ===
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-dev python-is-python3 \
      ffmpeg git curl libsndfile1 libgl1 build-essential \
 && rm -rf /var/lib/apt/lists/*

# === Copy requirements for pip caching ===
COPY requirements.txt .

# === Upgrade pip ===
RUN python3 -m pip install --upgrade pip

# === Install CUDA-compatible PyTorch stack ===
RUN python3 -m pip install \
      torch==2.0.1+cu118 \
      torchvision==0.15.2+cu118 \
      torchaudio==2.0.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

# === Install all other dependencies ===
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# === Install whisperx with diarization ===
RUN python3 -m pip install --no-cache-dir "git+https://github.com/m-bain/whisperx.git#egg=whisperx[diarization]"

# === Copy application code ===
COPY . .

# === Prepare runtime directories ===
RUN mkdir -p /app/transcripts /app/static/uploads /app/exports /app/logs

EXPOSE 8000

# === Launch the app ===
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
