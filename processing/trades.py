import numpy as np
import pandas as pd

def get_trades_Cp(
    tmp: pd.DataFrame,
    p: float = 0.2,
) -> pd.DataFrame:
    """
    Cp — доля объёма крупнейших агрессивных покупок
    по минутам.
    """

    # оставляем только агрессивные покупки
    tmp_buy = tmp[tmp["is_aggr_buy"]]

    if tmp_buy.empty:
        return pd.DataFrame(
            columns=["minute", "Cp"]
        )

    rows = []

    for minute_val, g in tmp_buy.groupby("minute"):
        q = g["qty"].values
        n = q.size

        if n == 0:
            Cp = 0.0
        else:
            k = max(1, int(np.floor(p * n)))
            q_sorted = np.sort(q)[::-1]
            Cp = q_sorted[:k].sum() / q_sorted.sum()

        rows.append((minute_val, Cp))

    return pd.DataFrame(
        rows,
        columns=["minute", "Cp"],
    )

def get_trades_entropy(
    tmp: pd.DataFrame,
) -> pd.DataFrame:

    # --- оставляем только агрессивные покупки
    df = tmp[tmp["is_aggr_buy"]]

    if df.empty:
        return pd.DataFrame(
            columns=["minute", "H_norm"]
        )

    rows = []

    for minute_val, g in df.groupby("minute", sort=True):
        q = g["qty"].values
        n = q.size

        if n <= 1:
            H_norm = 0.0
        else:
            q_sum = q.sum()
            if q_sum <= 0:
                H_norm = 0.0
            else:
                p = q / q_sum
                H = -np.sum(p * np.log(p))
                H_norm = H / np.log(n)

        rows.append((minute_val, H_norm))

    return pd.DataFrame(
        rows,
        columns=["minute", "H_norm"],
    )

def get_trades_Ceff(
    tmp: pd.DataFrame,
) -> pd.DataFrame:

    # --- оставляем только агрессивные покупки
    df = tmp[tmp["is_aggr_buy"]]

    if df.empty:
        return pd.DataFrame(
            columns=["minute", "C_eff"]
        )

    rows = []

    for minute_val, g in df.groupby("minute", sort=True):
        q = g["qty"].values
        n = q.size

        if n <= 1:
            C_eff = 0.0
        else:
            q_sum = q.sum()
            if q_sum <= 0:
                C_eff = 0.0
            else:
                p = q / q_sum
                Neff = 1.0 / np.sum(p * p)
                C_eff = Neff / n

        rows.append((minute_val, C_eff))

    return pd.DataFrame(
        rows,
        columns=["minute", "C_eff"],
    )
