import os
from dotenv import load_dotenv


SYMBOL = "ADAUSDT"
YC_BUCKET = "binance-data-downloader"
DAYS_BACK = 2
INTERVAL = "1m"
DATASET = "aggTrades"
# возможные значения:
# klines | aggTrades | trades | bookTicker

BASE_ROOT = "https://data.binance.vision/data/futures/um/daily"
SOURCE = "aggTrades"

DATA_ROOT = r"C:\projects\binance-data-downloader\data\raw"

DATASETS = {
    "klines": {
        # URL
        "source": "klines",
        "has_interval": True,
        "file_pattern": "{symbol}-{interval}-{date}.zip",

        # schema
        "columns": [
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
            "taker_buy_quote",
        ],
        "time_column": "open_time",
        "time_unit": "ms",

        # storage
        "storage_prefix": "klines_raw",
    },

    "aggTrades": {
        "source": "aggTrades",
        "has_interval": False,
        "file_pattern": "{symbol}-aggTrades-{date}.zip",

        "columns": [
            "agg_trade_id",
            "price",
            "quantity",
            "first_trade_id",
            "last_trade_id",
            "transact_time",
            "is_buyer_maker",
        ],
        "time_column": "transact_time",
        "time_unit": "ms",

        "storage_prefix": "agg_trades_raw",
    },

    "bookTicker": {
        "source": "bookTicker",
        "has_interval": False,
        "file_pattern": "{symbol}-bookTicker-{date}.zip",

        "columns": [
            "update_id",
            "best_bid_price",
            "best_bid_qty",
            "best_ask_price",
            "best_ask_qty",
            "transact_time",
            "event_time",
        ],
        # основной таймлайн — момент обновления стакана
        "time_column": "event_time",
        "time_unit": "ms",

        "storage_prefix": "bookTicker_raw",
    },

    "indexPriceKlines": {
        "source": "indexPriceKlines",
        "has_interval": True,
        "file_pattern": "{symbol}-indexPriceKlines-{interval}-{date}.zip",

        "columns": [
            "open_time",
            "open",
            "high",
            "low",
            "close",
        ],
        "time_column": "open_time",
        "time_unit": "ms",

        "storage_prefix": "indexPriceKlines_raw",
    },

    "markPriceKlines": {
        "source": "markPriceKlines",
        "has_interval": True,
        "file_pattern": "{symbol}-markPriceKlines-{interval}-{date}.zip",

        "columns": [
            "open_time",
            "open",
            "high",
            "low",
            "close",
        ],
        "time_column": "open_time",
        "time_unit": "ms",

        "storage_prefix": "markPriceKlines_raw",
    },

    "premiumIndexKlines": {
        "source": "premiumIndexKlines",
        "has_interval": True,
        "file_pattern": "{symbol}-premiumIndexKlines-{interval}-{date}.zip",

        "columns": [
            "open_time",
            "open",
            "high",
            "low",
            "close",
        ],
        "time_column": "open_time",
        "time_unit": "ms",

        "storage_prefix": "premiumIndexKlines_raw",
    },

    "trades": {
        "source": "trades",
        "has_interval": False,
        "file_pattern": "{symbol}-trades-{date}.zip",

        "columns": [
            "id",
            "price",
            "qty",
            "quote_qty",
            "transact_time",
            "is_buyer_maker",
        ],
        "time_column": "transact_time",
        "time_unit": "ms",

        "storage_prefix": "trades_raw",
    },
}





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