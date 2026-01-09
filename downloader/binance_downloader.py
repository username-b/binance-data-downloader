import os
import io
import zipfile
import requests
from datetime import date
from typing import List, Optional

import pandas as pd

from utils.logger import get_logger
from config import BINANCE_BASE_URL, DATA_SOURCES
from processing.column_names import COLUMN_NAMES


logger = get_logger(__name__)


def _download_and_extract_csv(url: str) -> Optional[pd.DataFrame]:
    """
    Скачивает zip-файл и извлекает CSV в DataFrame.
    """
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return None

        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                df = pd.read_csv(f, header=0, low_memory=False)

        return df

    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return None


def _normalize_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Приведение имён и типов колонок.
    """
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    if source in COLUMN_NAMES:
        target = COLUMN_NAMES[source]
        k = min(len(target), df.shape[1])
        df.columns = target[:k]
        df = df[target[:k]]

    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="ignore")

    return df


def download_daily_data(
    symbol: str,
    interval: str,
    day: date,
    output_dir: str,
) -> List[str]:
    """
    Загружает ВСЕ источники данных Binance за один день.
    Возвращает список путей к сохранённым CSV.
    """

    y = day.year
    m = f"{day.month:02d}"
    d = f"{day.day:02d}"

    saved_files: List[str] = []

    day_dir = os.path.join(output_dir, symbol, day.isoformat())
    os.makedirs(day_dir, exist_ok=True)

    for source, source_interval in DATA_SOURCES.items():
        if source_interval:
            path = f"{BINANCE_BASE_URL}/{source}/{symbol}/{source_interval}"
            file_name = f"{symbol}-{source_interval}-{y}-{m}-{d}.zip"
        else:
            path = f"{BINANCE_BASE_URL}/{source}/{symbol}"
            file_name = f"{symbol}-{source}-{y}-{m}-{d}.zip"

        url = f"{path}/{file_name}"
        logger.debug(f"Downloading {url}")

        df = _download_and_extract_csv(url)
        if df is None or df.empty:
            continue

        df = _normalize_columns(df, source)

        out_path = os.path.join(day_dir, f"{source}.csv")
        df.to_csv(out_path, index=False)

        saved_files.append(out_path)

        # освобождаем память
        del df

    if not saved_files:
        logger.warning(f"No data downloaded for {day}")

    return saved_files
