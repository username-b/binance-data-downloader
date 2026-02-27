SYMBOL = "ADAUSDT"
INTERVAL = "1m"

# <<< ВАЖНО >>>
FEATURE_SOURCE = "klines"  
# просто меняешь это значение

START_DATE = "2026-02-01"
END_DATE   = "2020-02-01"

RAW_PREFIX = {
    "klines": "klines_raw",
}

FEATURE_PREFIX = {
    "klines": "features_klines",
}

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