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
