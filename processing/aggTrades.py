import numpy as np
import pandas as pd

def get_L_last20s(tmp: pd.DataFrame) -> pd.DataFrame:
    """
    Коэффициент внутриминутной динамики L_last20s:
    отношение дельты агрессии за последние 20 секунд
    к полной дельте за минуту.
    """

    is_last20 = tmp["offset_ms"] >= 40_000

    total = (
        tmp.groupby("minute", as_index=False)["signed_qty"]
           .sum()
           .rename(columns={"signed_qty": "delta_total"})
    )

    last20 = (
        tmp[is_last20]
        .groupby("minute", as_index=False)["signed_qty"]
        .sum()
        .rename(columns={"signed_qty": "delta_last20"})
    )

    merged = total.merge(
        last20,
        on="minute",
        how="left",
    ).fillna(0.0)

    merged["L_last20s"] = np.divide(
        merged["delta_last20"],
        merged["delta_total"],
        out=np.zeros_like(merged["delta_total"]),
        where=merged["delta_total"] != 0,
    )

    return merged[
        [
            "minute",
            "L_last20s",
        ]
    ]

def get_aggTrades_delta(tmp: pd.DataFrame) -> pd.DataFrame:
    """
    Минутная дельта агрессии и нормализация.
    """

    grouped = (
        tmp.groupby("minute", sort=True, as_index=False)
           .agg(
               delta_v=("signed_qty", "sum"),
               volume=("abs_qty", "sum"),
           )
    )

    grouped["delta_v_norm"] = np.divide(
        grouped["delta_v"],
        grouped["volume"],
        out=np.zeros_like(grouped["delta_v"]),
        where=grouped["volume"] > 0,
    )

    return grouped[
        [
            "minute",
            "delta_v_norm",
        ]
    ]
