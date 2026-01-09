FROM python:3.10-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libstdc++6 \
    libgcc1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install --no-cache-dir \
    faster-whisper==1.0.3 \
    ctranslate2==4.5.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "asgi_dev:app", "--host", "0.0.0.0", "--port", "8000"]
