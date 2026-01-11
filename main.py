import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

from config import (
    SYMBOL,
    INTERVAL,
    START_DATE,
    END_DATE,
    RAW_DATA_DIR,
    PARQUET_DATA_DIR,
)

from utils.logger import get_logger
from utils.date_utils import daterange

from downloader.binance_downloader import download_daily_data
from processing.csv_loader import load_raw_csv

from processing.feature_engineering import (
    build_features_from_klines,
    build_features_from_index_price,
    build_features_from_mark_price,
    build_features_from_premium,
    build_features_from_trades,
    build_features_from_aggTrades,
    build_features_from_orderbook,
)

from storage.parquet_writer import write_parquet


logger = get_logger(__name__)


# =============================================================================
# Source detection
# =============================================================================

def detect_source(filename: str) -> str | None:
    name = filename.lower()

    if "aggtrades" in name:
        return "aggTrades"
    if "bookticker" in name:
        return "orderbook"
    if name.endswith("trades.csv"):
        return "trades"
    if "indexpriceklines" in name:
        return "index"
    if "markpriceklines" in name:
        return "mark"
    if "premiumindexklines" in name:
        return "premium"
    if "klines" in name:
        return "klines"

    return None


# =============================================================================
# Pipeline definition (STRICT DAG)
# =============================================================================

PRICE_SOURCES: dict[str, Callable] = {
    "index": build_features_from_index_price,
    "mark": build_features_from_mark_price,
    "premium": build_features_from_premium,
}

MICROSTRUCTURE_SOURCES: dict[str, Callable] = {
    "aggTrades": build_features_from_aggTrades,
    "trades": build_features_from_trades,
    "orderbook": build_features_from_orderbook,
}


# =============================================================================
# Validation helpers
# =============================================================================

def validate_feature_frame(df: pd.DataFrame, source: str) -> None:
    if "timestamp" not in df.columns:
        raise ValueError(f"{source}: missing column `timestamp`")

    if not pd.api.types.is_datetime64_ns_dtype(df["timestamp"]):
        raise TypeError(f"{source}: `timestamp` is not datetime64[ns]")

    if not df["timestamp"].is_unique:
        raise ValueError(f"{source}: `timestamp` is not unique")

    if not df["timestamp"].is_monotonic_increasing:
        raise ValueError(f"{source}: `timestamp` is not sorted")


# =============================================================================
# Core processing
# =============================================================================

def process_single_day(day: date) -> None:
    logger.info(f"Processing {day}")

    # -------------------------------------------------------------------------
    # 1. Download
    # -------------------------------------------------------------------------
    downloaded_files = download_daily_data(
        symbol=SYMBOL,
        interval=INTERVAL,
        day=day,
        output_dir=RAW_DATA_DIR,
    )

    if not downloaded_files:
        logger.warning(f"No files downloaded for {day}")
        return

    # -------------------------------------------------------------------------
    # 2. Index files by source
    # -------------------------------------------------------------------------
    files_by_source: dict[str, Path] = {}

    for file_path in downloaded_files:
        path = Path(file_path)
        source = detect_source(path.name)
        if source:
            files_by_source[source] = path

    # -------------------------------------------------------------------------
    # 3. KLINES — BASE TIME AXIS (MANDATORY)
    # -------------------------------------------------------------------------
    if "klines" not in files_by_source:
        logger.warning(f"Klines missing for {day}, skipping day")
        return

    try:
        df_raw = load_raw_csv(files_by_source["klines"])
        df_klines, df_close_ref = build_features_from_klines(df_raw)
        validate_feature_frame(df_klines, "klines")

        df_day = df_klines.copy()
    except Exception:
        logger.exception(f"Failed to process klines for {day}")
        return

    # -------------------------------------------------------------------------
    # 4. PRICE-BASED FEATURES (MERGE INTO KLINES)
    # -------------------------------------------------------------------------
    for source, builder in PRICE_SOURCES.items():
        if source not in files_by_source:
            continue

        try:
            df_raw = load_raw_csv(files_by_source[source])
            df_feat = builder(df_raw, df_close_ref)

            validate_feature_frame(df_feat, source)

            df_day = df_day.merge(
                df_feat,
                on="timestamp",
                how="left",
            )
        except Exception:
            logger.exception(f"Failed processing {source} for {day}")

    # -------------------------------------------------------------------------
    # 5. MICROSTRUCTURE FEATURES (OPTIONAL, MERGE)
    # -------------------------------------------------------------------------
    # Раскомментируй, когда builders будут готовы
    #
    # for source, builder in MICROSTRUCTURE_SOURCES.items():
    #     if source not in files_by_source:
    #         continue
    #
    #     try:
    #         df_raw = load_raw_csv(files_by_source[source])
    #
    #         if source == "aggTrades":
    #             df_feat = builder(df_raw, df_close_ref)
    #         else:
    #             df_feat = builder(df_raw)
    #
    #         validate_feature_frame(df_feat, source)
    #
    #         df_day = df_day.merge(
    #             df_feat,
    #             on="timestamp",
    #             how="left",
    #         )
    #     except Exception:
    #         logger.exception(f"Failed processing {source} for {day}")

    # -------------------------------------------------------------------------
    # 6. FINAL SANITY CHECK
    # -------------------------------------------------------------------------
    assert df_day["timestamp"].is_unique
    assert df_day["timestamp"].is_monotonic_increasing

    # -------------------------------------------------------------------------
    # 7. Persist
    # -------------------------------------------------------------------------
    write_parquet(
        df=df_day,
        symbol=SYMBOL,
        interval=INTERVAL,
        day=day,
        base_dir=PARQUET_DATA_DIR,
    )

    logger.info(f"Finished {day}")


# =============================================================================
# Entry point
# =============================================================================

def main() -> None:
    logger.info("Pipeline started")

    for day in daterange(START_DATE, END_DATE):
        try:
            process_single_day(day)
        except Exception:
            logger.exception(f"Unhandled failure on {day}")

    logger.info("Pipeline finished")


if __name__ == "__main__":
    main()
