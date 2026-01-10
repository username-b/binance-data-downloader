from datetime import date
from pathlib import Path


# ============================================================
# Источники данных Binance
# ============================================================

# None  -> данные без таймфрейма (aggTrades, trades, bookTicker)
# "1m"  -> минутные klines
DATA_SOURCES = {
    "klines": "1m",
    "aggTrades": None,
    "bookTicker": None,
    "indexPriceKlines": "1m",
    "markPriceKlines": "1m",
    "premiumIndexKlines": "1m",
    "trades": None,
}

# Базовый URL Binance Data Vision (USDT-M Futures)
BINANCE_BASE_URL = "https://data.binance.vision/data/futures/um/daily"


# ============================================================
# Параметры эксперимента
# ============================================================

# Торговый инструмент
SYMBOL = "ADAUSDT"

# Базовый таймфрейм моделирования
# (используется как референс для агрегаций)
INTERVAL = "1m"

# Период исследования
START_DATE = date(2020, 1, 1)
END_DATE = date(2020, 1, 3)

# ============================================================
# Пути хранения данных
# ============================================================

# Корень проекта (относительно config.py)
PROJECT_ROOT = Path(__file__).resolve().parent

# Сырые CSV из Binance
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Обработанные parquet (dataset)
PARQUET_DATA_DIR = PROJECT_ROOT / "data" / "parquet"


# ============================================================
# Параметры обработки
# ============================================================

# Минимально допустимое число минут в дне
# (для контроля качества данных)
MIN_MINUTES_PER_DAY = 1_400  # из 1440

# Сортировка обязательна перед сохранением
SORT_BY_TIMESTAMP = True

# Колонка времени (единый стандарт по проекту)
TIMESTAMP_COLUMN = "timestamp"

# Тип времени: миллисекунды Unix Epoch
TIMESTAMP_UNIT = "ms"
