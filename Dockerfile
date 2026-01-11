FROM python:3.11-slim

# ====== system deps ======
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ====== python deps ======
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ====== project ======
COPY . .

# ====== env ======
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ====== default cmd ======
CMD ["python", "-m", "binance_downloader"]
