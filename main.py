import gc
import config

from builders import BUILDERS
from readers.parquet_reader import ParquetDayReader
from storage.yandex import YandexObjectStorage
from utils.dates import daterange


# --- выбор билдера ТОЛЬКО из конфига
if config.FEATURE_SOURCE not in BUILDERS:
    raise ValueError(
        f"Unknown FEATURE_SOURCE: {config.FEATURE_SOURCE}"
    )

builder = BUILDERS[config.FEATURE_SOURCE]
reader = ParquetDayReader(raw_storage)

raw_storage = YandexObjectStorage(
    bucket=config.YC_BUCKET,
    prefix=config.RAW_PREFIX[builder.source],
)

feature_storage = YandexObjectStorage(
    bucket=config.YC_BUCKET,
    prefix=config.FEATURE_PREFIX[builder.source],
)

reader = ParquetDayReader(
    storage=raw_storage,
    prefix=config.RAW_PREFIX[builder.source],
)

for date in daterange(config.START_DATE, config.END_DATE):

    df_raw = reader.read_day(
        config.SYMBOL,
        config.INTERVAL,
        date,
    )

    if df_raw is None or df_raw.empty:
        continue

    df_feat = builder.build(df_raw)

    feature_storage.write_parquet(
        df_feat,
        key=f"{config.SYMBOL}-{config.INTERVAL}-{date}.parquet",
    )

    del df_raw, df_feat
    gc.collect()
