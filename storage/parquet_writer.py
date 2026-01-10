from pathlib import Path
from datetime import date
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def _build_parquet_path(
    base_dir: Path,
    symbol: str,
    interval: str,
    day: date,
) -> Path:
    """
    Формирует путь вида:
    base_dir/symbol=BTCUSDT/interval=1m/year=2021/month=01/2021-01-01.parquet
    """
    return (
        base_dir
        / f"symbol={symbol}"
        / f"interval={interval}"
        / f"year={day.year}"
        / f"month={day.month:02d}"
        / f"{day.isoformat()}.parquet"
    )


def write_parquet(
    df: pd.DataFrame,
    symbol: str,
    interval: str,
    day: date,
    base_dir: str | Path,
    schema: Optional[pa.Schema] = None,
    compression: str = "zstd",
) -> None:
    """
    Сохраняет дневной DataFrame в parquet.

    Параметры:
    ----------
    df : pd.DataFrame
        Минутные данные за один день (уже агрегированные и отсортированные).
    symbol : str
        Торговый инструмент (например, BTCUSDT).
    interval : str
        Таймфрейм (например, 1m).
    day : date
        Дата данных.
    base_dir : str | Path
        Корневая директория parquet-хранилища.
    schema : pa.Schema, optional
        Явная Arrow-схема (рекомендуется для стабильности типов).
    compression : str
        Тип сжатия (zstd / snappy / gzip).
    """

    if df.empty:
        # Пустые дни сознательно не пишем
        return

    base_dir = Path(base_dir)
    path = _build_parquet_path(base_dir, symbol, interval, day)
    path.parent.mkdir(parents=True, exist_ok=True)

    # --- Конвертация в Arrow Table
    if schema is not None:
        table = pa.Table.from_pandas(
            df,
            schema=schema,
            preserve_index=False,
        )
    else:
        table = pa.Table.from_pandas(
            df,
            preserve_index=False,
        )

    # --- Запись parquet
    pq.write_table(
        table,
        path,
        compression=compression,
        use_dictionary=True,
        write_statistics=True,
    )
