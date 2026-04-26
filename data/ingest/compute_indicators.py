"""
Compute technical indicators for each stock symbol using pandas-ta.
Indicators: RSI(14), MACD, Bollinger Bands(20), SMA(20), SMA(50),
            EMA(12), EMA(26), ATR(14), OBV.
"""

import pandas as pd
import pandas_ta as ta


def compute_indicators(ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators for each symbol in the OHLCV DataFrame.

    Args:
        ohlcv_df: DataFrame with columns symbol, date, open, high, low, close, volume

    Returns:
        DataFrame matching the technical_indicators table schema:
        symbol, date, rsi_14, macd_line, macd_signal, macd_hist,
        bb_upper, bb_middle, bb_lower, sma_20, sma_50, ema_12, ema_26,
        atr_14, obv
    """
    if ohlcv_df.empty:
        return pd.DataFrame()

    all_indicators = []

    symbols = ohlcv_df["symbol"].unique()
    print(f"Computing indicators for {len(symbols)} symbols...")

    for i, symbol in enumerate(symbols):
        df = ohlcv_df[ohlcv_df["symbol"] == symbol].copy()
        df = df.sort_values("date").reset_index(drop=True)

        if len(df) < 50:
            print(f"  Skipping {symbol}: only {len(df)} rows (need >= 50)")
            continue

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        rsi = ta.rsi(df["close"], length=14)
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        bbands = ta.bbands(df["close"], length=20, std=2)
        sma_20 = ta.sma(df["close"], length=20)
        sma_50 = ta.sma(df["close"], length=50)
        ema_12 = ta.ema(df["close"], length=12)
        ema_26 = ta.ema(df["close"], length=26)
        atr = ta.atr(df["high"], df["low"], df["close"], length=14)
        obv = ta.obv(df["close"], df["volume"])

        for idx in range(len(df)):
            row = {
                "symbol": symbol,
                "date": df.iloc[idx]["date"],
                "rsi_14": _safe_round(rsi, idx),
                "macd": _safe_round(macd.iloc[:, 0] if macd is not None else None, idx),
                "macd_signal": _safe_round(macd.iloc[:, 1] if macd is not None else None, idx),
                "macd_hist": _safe_round(macd.iloc[:, 2] if macd is not None else None, idx),
                "bb_upper": _safe_round(bbands.iloc[:, 2] if bbands is not None else None, idx),
                "bb_middle": _safe_round(bbands.iloc[:, 1] if bbands is not None else None, idx),
                "bb_lower": _safe_round(bbands.iloc[:, 0] if bbands is not None else None, idx),
                "sma_20": _safe_round(sma_20, idx),
                "sma_50": _safe_round(sma_50, idx),
                "ema_12": _safe_round(ema_12, idx),
                "ema_26": _safe_round(ema_26, idx),
                "atr_14": _safe_round(atr, idx),
                "obv": _safe_round(obv, idx, decimals=0),
            }
            all_indicators.append(row)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(symbols)} symbols")

    result = pd.DataFrame(all_indicators)
    print(f"Computed {len(result)} indicator rows.")
    return result


def _safe_round(series, idx: int, decimals: int = 4):
    """Safely extract and round a value from a pandas Series."""
    if series is None:
        return None
    try:
        val = series.iloc[idx]
        if pd.isna(val):
            return None
        rounded = round(float(val), decimals)
        if decimals == 0:
            return int(rounded)
        return rounded
    except (IndexError, TypeError):
        return None


if __name__ == "__main__":
    from data.ingest.fetch_ohlcv import fetch_ohlcv

    ohlcv = fetch_ohlcv(days=365)
    indicators = compute_indicators(ohlcv)
    print(indicators.head())
    print(indicators.dtypes)
