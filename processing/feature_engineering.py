import numpy as np
import pandas as pd

from aggTrades import get_L_last20s, get_aggTrades_delta
from trades import get_trades_Cp

def build_features_from_klines(df_klines: pd.DataFrame):
    """
    Оптимизированная версия:
    - timestamp ожидается в индексе
    - без copy / reset_index
    - NumPy для базовой математики
    - pandas только для rolling
    """

    close = df_klines["close"].to_numpy()
    open_ = df_klines["open"].to_numpy()
    high = df_klines["high"].to_numpy()
    low = df_klines["low"].to_numpy()
    volume = df_klines["volume"].to_numpy()
    quote_volume = df_klines["quote_volume"].to_numpy()
    taker_buy_volume = df_klines["taker_buy_volume"].to_numpy()

    # --- 1. лог-доходности
    log_close = np.log(close)
    log_return = np.diff(log_close, prepend=np.nan)

    # --- 2. ценовые диапазоны
    hl_range = (high - low) / close
    oc_return = (close - open_) / open_

    # --- 3. объёмы
    volume_log = np.log1p(volume)
    quote_volume_log = np.log1p(quote_volume)

    taker_buy_ratio = taker_buy_volume / np.where(volume == 0, np.nan, volume)

    # --- 4. волатильность (rolling остаётся pandas)
    log_return_s = pd.Series(log_return, index=df_klines.index)

    volatility_5m = (
        log_return_s.rolling(5, min_periods=2).std().to_numpy()
    )
    volatility_15m = (
        log_return_s.rolling(15, min_periods=2).std().to_numpy()
    )

    # --- 5. итоговый DataFrame
    df_features = pd.DataFrame(
        {
            "timestamp": df_klines.index,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "quote_volume": quote_volume,
            "log_return": log_return,
            "hl_range": hl_range,
            "oc_return": oc_return,
            "volume_log": volume_log,
            "quote_volume_log": quote_volume_log,
            "taker_buy_ratio": taker_buy_ratio,
            "volatility_5m": volatility_5m,
            "volatility_15m": volatility_15m,
        },
        index=df_klines.index,
    )

    # --- 6. close reference без copy
    df_close_ref = df_features[["close"]]

    return df_features, df_close_ref


def build_features_from_index_price(
    df_index: pd.DataFrame,
    df_close_ref: pd.DataFrame,
) -> pd.DataFrame:
    """
    Оптимизированная версия:
    - join по индексу
    - NumPy для арифметики
    - без лишних copy
    - готово для chunk / streaming
    Ожидается:
    - timestamp уже в индексе
    - данные отсортированы
    """

    # --- 1. join по индексу
    df = df_index.join(
        df_close_ref[["close"]].rename(columns={"close": "close_spot"}),
        how="left",
    )

    close = df["close"].to_numpy()
    close_spot = df["close_spot"].to_numpy()

    # --- 2. отклонение индексной цены
    index_diff = close - close_spot

    out = pd.DataFrame(
        {
            "timestamp": df.index,
            "index_diff": index_diff,
            "index_diff_pct": index_diff / close_spot,
            "index_log_ratio": np.log(close / close_spot),
            "index_diff_change": np.diff(index_diff, prepend=np.nan),
        },
        index=df.index,
    )

    return out


def build_features_from_mark_price(
    df_mark: pd.DataFrame,
    df_close_ref: pd.DataFrame,
) -> pd.DataFrame:
    """
    Оптимизированная версия:
    - join по индексу вместо merge
    - без лишних copy
    - timestamp ожидается в индексе
    """

    # --- 1. join по индексу
    df = df_mark.join(
        df_close_ref[["close"]].rename(columns={"close": "close_spot"}),
        how="left",
    )

    close = df["close"].to_numpy()
    close_spot = df["close_spot"].to_numpy()

    # --- 2. базовое отклонение mark
    mark_diff = close - close_spot

    # --- 3. EMA считаем через pandas (C-оптимизировано)
    mark_diff_s = pd.Series(mark_diff, index=df.index)

    out = pd.DataFrame(
        {
            "timestamp": df.index,
            "mark_diff": mark_diff,
            "mark_diff_pct": mark_diff / close_spot,
            "mark_log_ratio": np.log(close / close_spot),
            "mark_diff_ema_5": mark_diff_s.ewm(span=5, adjust=False).mean(),
            "mark_diff_ema_15": mark_diff_s.ewm(span=15, adjust=False).mean(),
        },
        index=df.index,
    )

    return out


def build_features_from_premium(
    df_premium: pd.DataFrame,
    df_close_ref: pd.DataFrame,
) -> pd.DataFrame:
    """
    Быстрая версия:
    - без merge
    - без лишних copy
    - рассчитана на chunk-обработку
    Ожидается, что:
    - timestamp уже есть
    - timestamp отсортирован
    """

    # --- 1. join по индексу (в 2–3 раза быстрее merge)
    df = df_premium.join(
        df_close_ref[["close"]].rename(columns={"close": "close_spot"}),
        how="left",
    )

    close = df["close"].to_numpy()
    close_spot = df["close_spot"].to_numpy()

    # --- 2. премия
    premium = close - close_spot

    # --- 3. формирование фичей
    out = pd.DataFrame(
        {
            "timestamp": df.index,
            "premium": premium,
            "premium_pct": premium / close_spot,
            "premium_log_ratio": np.log(close / close_spot),
            "premium_change": np.diff(premium, prepend=np.nan),
            "premium_vol_5": (
                pd.Series(premium)
                .rolling(5, min_periods=2)
                .std()
                .to_numpy()
            ),
        },
        index=df.index,
    )

    return out


def build_features_from_aggTrades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Общий билдер фичей из aggTrades.
    Считает:
    - delta_v_norm
    - L_last20s
    """

    # --- общая numpy-предобработка (ОДИН РАЗ)
    transact_time = df["transact_time"].values
    qty = df["quantity"].astype("float64").values
    is_sell = df["isBuyerMaker"].astype(bool).values

    minute = transact_time // 60_000
    offset_ms = transact_time % 60_000

    signed_qty = np.where(is_sell, -qty, qty)

    tmp = pd.DataFrame(
        {
            "minute": minute,
            "signed_qty": signed_qty,
            "abs_qty": qty,
            "offset_ms": offset_ms,
        }
    )

    # --- фичи
    df_delta = get_aggTrades_delta(tmp)
    df_L = get_L_last20s(tmp)

    # --- объединение
    grouped = (
        df_delta
        .merge(df_L, on="minute", how="left")
    )

    grouped["timestamp"] = pd.to_datetime(
        grouped["minute"] * 60_000,
        unit="ms",
    )

    grouped.sort_values("timestamp", inplace=True)

    return grouped[
        [
            "timestamp",
            "L_last20s",
            "delta_v_norm",
        ]
    ]

def build_features_from_trades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Общий билдер фичей из aggTrades.
    Считает:
    - delta_v_norm
    - L_last20s
    """

    # --- общая numpy-предобработка (ОДИН РАЗ)
    transact_time = df["transact_time"].values
    qty = df["quantity"].astype("float64").values
    is_sell = df["isBuyerMaker"].astype(bool).values

    minute = transact_time // 60_000
    offset_ms = transact_time % 60_000

    signed_qty = np.where(is_sell, -qty, qty)

    tmp = pd.DataFrame(
        {
            "minute": minute,
            "signed_qty": signed_qty,
            "abs_qty": qty,
            "offset_ms": offset_ms,
        }
    )

    # --- фичи
    df_delta = get_aggTrades_delta(tmp)
    df_L = get_L_last20s(tmp)

    # --- объединение
    grouped = (
        df_delta
        .merge(df_L, on="minute", how="left")
    )

    grouped["timestamp"] = pd.to_datetime(
        grouped["minute"] * 60_000,
        unit="ms",
    )

    grouped.sort_values("timestamp", inplace=True)

    return grouped[
        [
            "timestamp",
            "L_last20s",
            "delta_v_norm",
        ]
    ]

def build_features_from_trades(
    df: pd.DataFrame,
    p: float = 0.2,
) -> pd.DataFrame:
    """
    Общий билдер фичей из trades.
    Сейчас считает:
    - Cp (Top-p% агрессивных покупок)
    """

    # --- общая numpy-предобработка (ОДИН РАЗ)
    trade_time = df["time"].values
    qty = df["qty"].astype("float64").values
    is_sell = df["isBuyerMaker"].astype(bool).values

    minute = trade_time // 60_000

    # агрессивные покупки: seller is maker -> False
    is_aggr_buy = ~is_sell

    tmp = pd.DataFrame(
        {
            "minute": minute,
            "qty": qty,
            "is_aggr_buy": is_aggr_buy,
        }
    )

    # --- фича Cp
    df_cp = get_trades_Cp(tmp, p=p)

    if df_cp.empty:
        return pd.DataFrame(
            columns=["timestamp", "Cp"]
        )

    # --- timestamp
    df_cp["timestamp"] = pd.to_datetime(
        df_cp["minute"] * 60_000,
        unit="ms",
    )

    df_cp.sort_values("timestamp", inplace=True)

    return df_cp[
        [
            "timestamp",
            "Cp",
        ]
    ]
