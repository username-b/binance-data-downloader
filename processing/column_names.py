# === Словари имен столбцов по источнику ===

column_names = {
    "klines": [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count", "taker_buy_volume",
        "taker_buy_quote_volume", "ignore"
    ],
    "indexPriceKlines": [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count", "taker_buy_volume",
        "taker_buy_quote_volume", "ignore"
    ],
    "markPriceKlines": [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count", "taker_buy_volume",
        "taker_buy_quote_volume", "ignore"
    ],
    "premiumIndexKlines": [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count", "taker_buy_volume",
        "taker_buy_quote_volume", "ignore"
    ],
    "aggTrades": [
        "agg_trade_id", "price", "qty", "first_trade_id", "last_trade_id", "timestamp", "is_buyer_maker"
    ],
    "trades": [
        "trade_id", "price", "qty", "quote_qty", "timestamp", "is_buyer_maker", "is_best_match"
    ],
    "metrics": [
        "timestamp", "open_interest", "funding_rate", "long_account_ratio", "short_account_ratio"
    ]
}
