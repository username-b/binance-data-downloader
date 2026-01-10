from datetime import date
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
from processing.feature_engineering import (build_features_from_klines, build_features_from_index_price, 
                                            build_features_from_mark_price, build_features_from_premium, 
                                            build_features_from_trades, build_features_from_aggTrades,
                                            build_features_from_orderbook)
from storage.parquet_writer import write_parquet

logger = get_logger(__name__)


def process_single_day(day: date) -> None:
    """
    Полный цикл обработки одного дня:
    download → load → aggregate → feature engineering → parquet
    """

    logger.info(f"Processing {day}")

    # 1. Скачивание CSV за день
    csv_files = download_daily_data(
        symbol=SYMBOL,
        interval=INTERVAL,
        day=day,
        output_dir=RAW_DATA_DIR,
    )

    if not csv_files:
        logger.warning(f"No data for {day}")
        return

    # 2. Последовательная обработка файлов
    df_close_ref = None          # close классических свечей
    daily_frames = []            # все фичи за день

    for csv_path in csv_files:
        name = csv_path.name.lower()
        logger.debug(f"Processing {name}")

        df_raw = load_raw_csv(csv_path)

        # --- 1. Классические свечи (ОБЯЗАТЕЛЬНО ПЕРВЫМИ)
        if "klines" in name and "index" not in name and "mark" not in name:
            df_features, df_close_ref = build_features_from_klines(df_raw)
            daily_frames.append(df_features)

        # --- 2. Производные минутные цены
        elif "indexpriceklines" in name:
            df_features = build_features_from_index_price(df_raw, df_close_ref)
            daily_frames.append(df_features)

        elif "markpriceklines" in name:
            df_features = build_features_from_mark_price(df_raw, df_close_ref)
            daily_frames.append(df_features)

        elif "premiumindexklines" in name:
            df_features = build_features_from_premium(df_raw, df_close_ref)
            daily_frames.append(df_features)

        # --- 3. Тиковые данные → агрегация → фичи
        elif "aggtrades" in name:
            df_features = build_features_from_aggTrades(df_raw, df_close_ref)
            daily_frames.append(df_features)

        elif "trades" in name:
            df_features = build_features_from_trades(df_raw, df_close_ref)
            daily_frames.append(df_features)

        elif "bookticker" in name:
            df_features = build_features_from_orderbook(df_raw, df_close_ref)
            daily_frames.append(df_features)

        else:
            logger.warning(f"Unknown file type: {csv_path}")

        del df_raw


    if not daily_frames:
        logger.warning(f"No processed data for {day}")
        return

    # 3. Объединение ВНУТРИ дня (это безопасно)
    logger.debug(f"Merging daily data for {day}")
    df_day = (
        daily_frames[0]
        if len(daily_frames) == 1
        else daily_frames[0].append(daily_frames[1:], ignore_index=True)
    )

    df_day.sort_values("timestamp", inplace=True)

    # 4. Сохранение parquet
    write_parquet(
        df=df_day,
        symbol=SYMBOL,
        interval=INTERVAL,
        day=day,
        base_dir=PARQUET_DATA_DIR,
    )

    logger.info(f"Finished {day}")


def main() -> None:
    logger.info("Pipeline started")

    for day in daterange(START_DATE, END_DATE):
        try:
            process_single_day(day)
        except Exception as e:
            logger.exception(f"Failed processing {day}: {e}")

    logger.info("Pipeline finished")


if __name__ == "__main__":
    main()
