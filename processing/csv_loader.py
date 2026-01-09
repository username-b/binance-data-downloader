import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def load_raw_csv(
    path: str,
    *,
    expected_columns: list[str] | None = None,
    timestamp_col: str | None = None,
) -> pd.DataFrame:
    """
    Загружает CSV-файл в DataFrame с гарантированным schema.
    НЕ агрегирует и НЕ считает фичи.
    """

    logger.debug(f"Loading CSV: {path}")

    df = pd.read_csv(
        path,
        low_memory=False,
    )

    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns {missing} in {path}")
        df = df[expected_columns]

    if timestamp_col:
        df[timestamp_col] = pd.to_numeric(df[timestamp_col], errors="coerce")
        df = df.dropna(subset=[timestamp_col])
        df[timestamp_col] = df[timestamp_col].astype("int64")

        df = df.sort_values(timestamp_col)

    df = df.reset_index(drop=True)

    return df
