
SYMBOL = "ADAUSDT"
YC_BUCKET = "binance-data-downloader"
DAYS_BACK = 7
INTERVAL = "1m"

BASE_ROOT = "https://data.binance.vision/data/futures/um/daily"
SOURCE = "klines"

DATA_ROOT = r"C:\projects\binance-data-downloader\data\raw"

KLINES_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote"
]


import os
from dotenv import load_dotenv

load_dotenv()  # загружает .env

# =========================
# YANDEX OBJECT STORAGE
# =========================
YC_ACCESS_KEY_ID = os.getenv("YC_ACCESS_KEY_ID")
YC_SECRET_ACCESS_KEY = os.getenv("YC_SECRET_ACCESS_KEY")
YC_REGION = os.getenv("YC_REGION", "ru-central1")
YC_ENDPOINT = os.getenv("YC_ENDPOINT")
YC_BUCKET = os.getenv("YC_BUCKET")

# =========================
# VALIDATION (очень важно)
# =========================
_required = {
    "YC_ACCESS_KEY_ID": YC_ACCESS_KEY_ID,
    "YC_SECRET_ACCESS_KEY": YC_SECRET_ACCESS_KEY,
    "YC_ENDPOINT": YC_ENDPOINT,
    "YC_BUCKET": YC_BUCKET,
}

missing = [k for k, v in _required.items() if not v]
if missing:
    raise RuntimeError(f"Missing required env vars: {missing}")