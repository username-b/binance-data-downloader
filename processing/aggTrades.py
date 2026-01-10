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

def get_aggTrades_FPI(
    tmp: pd.DataFrame,
) -> pd.DataFrame:

    if tmp.empty:
        return pd.DataFrame(
            columns=["minute", "F_PI"]
        )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        p = g["price"].values
        q = g["qty"].values
        sign = g["sign"].values

        if p.size <= 1:
            F_PI = 0.0
        else:
            q_sum = q.sum()
            if q_sum <= 0:
                F_PI = 0.0
            else:
                # --- VWAP
                vwap = np.sum(p * q) / q_sum

                # --- Price Impact
                PI = np.sum(sign * q * (p - vwap))

                # --- внутриминутная волатильность
                log_p = np.log(p)
                sigma = np.sqrt(
                    np.sum((log_p - log_p.mean()) ** 2)
                )

                denom = q_sum * sigma

                if denom > 0:
                    F_PI = PI / denom
                else:
                    F_PI = 0.0

        rows.append((minute_val, F_PI))

    return pd.DataFrame(
        rows,
        columns=["minute", "F_PI"],
    )

def get_aggTrades_Feff(
    tmp: pd.DataFrame,
    close_ref: pd.DataFrame,
) -> pd.DataFrame:

    if tmp.empty or close_ref.empty:
        return pd.DataFrame(
            columns=["minute", "F_eff"]
        )

    # --- close как minute-indexed DataFrame
    close_map = (
        close_ref[["minute", "close"]]
        .drop_duplicates("minute")
        .set_index("minute")["close"]
    )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        if minute_val not in close_map.index:
            continue

        p = g["price"].values
        q = g["qty"].values
        sign = g["sign"].values

        q_sum = q.sum()
        if q_sum <= 0:
            F_eff = 0.0
        else:
            # --- VWAP
            vwap = np.sum(p * q) / q_sum

            # --- агрессивные объёмы
            V_buy = q[sign > 0].sum()
            V_sell = q[sign < 0].sum()

            delta_V = V_buy - V_sell

            if delta_V == 0:
                F_eff = 0.0
            else:
                close = close_map.loc[minute_val]
                F_eff = (close - vwap) / abs(delta_V)

        rows.append((minute_val, F_eff))

    return pd.DataFrame(
        rows,
        columns=["minute", "F_eff"],
    )

def get_aggTrades_Fasym(
    tmp: pd.DataFrame,
) -> pd.DataFrame:

    if tmp.empty:
        return pd.DataFrame(
            columns=["minute", "F_asym"]
        )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        p = g["price"].values
        q = g["qty"].values
        sign = g["sign"].values

        q_sum = q.sum()
        if q_sum <= 0:
            F_asym = 0.0
        else:
            # --- VWAP
            vwap = np.sum(p * q) / q_sum

            # --- price impact по сторонам
            diff = p - vwap

            PI_buy = np.sum(q[sign > 0] * diff[sign > 0])
            PI_sell = np.sum(q[sign < 0] * diff[sign < 0])

            num = abs(PI_buy) - abs(PI_sell)
            den = abs(PI_buy) + abs(PI_sell)

            if den > 0:
                F_asym = num / den
            else:
                F_asym = 0.0

        rows.append((minute_val, F_asym))

    return pd.DataFrame(
        rows,
        columns=["minute", "F_asym"],
    )

def get_aggTrades_Flate(
    tmp: pd.DataFrame,
) -> pd.DataFrame:

    if tmp.empty:
        return pd.DataFrame(
            columns=["minute", "F_late"]
        )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        p = g["price"].values
        q = g["qty"].values
        sign = g["sign"].values
        offset = g["offset_ms"].values

        q_sum = q.sum()
        if q_sum <= 0:
            F_late = 0.0
        else:
            # --- общий VWAP за минуту
            vwap = np.sum(p * q) / q_sum

            diff = p - vwap

            # --- PI за всю минуту
            PI_total = np.sum(sign * q * diff)

            if PI_total == 0:
                F_late = 0.0
            else:
                # --- PI за последние 20 секунд
                mask_last20 = offset >= 40_000
                PI_last = np.sum(sign[mask_last20] *
                                 q[mask_last20] *
                                 diff[mask_last20])

                F_late = PI_last / PI_total

        rows.append((minute_val, F_late))

    return pd.DataFrame(
        rows,
        columns=["minute", "F_late"],
    )


def get_aggTrades_RV(
    tmp: pd.DataFrame,
) -> pd.DataFrame:

    if tmp.empty:
        return pd.DataFrame(
            columns=["minute", "RV"]
        )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        if g.shape[0] <= 1:
            RV = 0.0
        else:
            # --- сортировка по времени / порядку
            g_sorted = g.sort_values("order_idx")

            p = g_sorted["price"].values

            dp = np.diff(p)
            RV = np.sum(dp * dp)

        rows.append((minute_val, RV))

    return pd.DataFrame(
        rows,
        columns=["minute", "RV"],
    )