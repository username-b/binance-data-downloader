import pandas as pd
from .base import FeatureBuilder


class KlinesBuilder(FeatureBuilder):

    source = "klines"
    needs_reference = False

    REQUIRED_COLUMNS = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
    ]

    def build(
        self,
        df_raw: pd.DataFrame,
        df_ref: pd.DataFrame | None = None,
    ) -> pd.DataFrame:

        missing = set(self.REQUIRED_COLUMNS) - set(df_raw.columns)
        if missing:
            raise ValueError(f"Klines missing columns: {missing}")

        df = df_raw[self.REQUIRED_COLUMNS].copy()

        df["timestamp"] = pd.to_datetime(
            df["open_time"],
            unit="ms",
        )

        df = (
            df.drop_duplicates(subset=["timestamp"])
              .sort_values("timestamp")
        )

        return df[
            [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "quote_volume",
            ]
        ]
