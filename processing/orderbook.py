import numpy as np
import pandas as pd


def get_orderbook_Uimb(
    tmp: pd.DataFrame,
) -> pd.DataFrame:
    """
    Баланс обновлений лучших котировок:
    U_imb = (N_bid - N_ask) / (N_bid + N_ask)
    """

    if tmp.empty:
        return pd.DataFrame(
            columns=["minute", "U_imb"]
        )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        N_bid = int(g["bid_change"].sum())
        N_ask = int(g["ask_change"].sum())

        denom = N_bid + N_ask
        if denom > 0:
            U_imb = (N_bid - N_ask) / denom
        else:
            U_imb = 0.0

        rows.append((minute_val, U_imb))

    return pd.DataFrame(
        rows,
        columns=["minute", "U_imb"],
    )

def get_orderbook_tau_ratio(
    tmp: pd.DataFrame,
) -> pd.DataFrame:
    """
    Отношение медианных времен жизни лучших котировок:
    tau_ratio = median(tau_bid) / median(tau_ask)
    """

    if tmp.empty:
        return pd.DataFrame(
            columns=["minute", "tau_ratio"]
        )

    rows = []

    for minute_val, g in tmp.groupby("minute", sort=True):
        bid_tau = g["bid_lifetime"].values
        ask_tau = g["ask_lifetime"].values

        # оставляем только ненулевые времена
        bid_tau = bid_tau[bid_tau > 0]
        ask_tau = ask_tau[ask_tau > 0]

        if bid_tau.size == 0 or ask_tau.size == 0:
            tau_ratio = 0.0
        else:
            med_bid = np.median(bid_tau)
            med_ask = np.median(ask_tau)

            if med_ask > 0:
                tau_ratio = med_bid / med_ask
            else:
                tau_ratio = 0.0

        rows.append((minute_val, tau_ratio))

    return pd.DataFrame(
        rows,
        columns=["minute", "tau_ratio"],
    )
