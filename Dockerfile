FROM ubuntu:22.04

# Install Python 3.11 + system dependencies (NO PPA)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-distutils python3-pip \
    ffmpeg git curl build-essential \
    libpq-dev libxml2-dev libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

# Set python aliases
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
 && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r /app/requirements.txt

COPY . /app

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && sed -i 's/\r$//' /entrypoint.sh

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=12 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/healthz" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
