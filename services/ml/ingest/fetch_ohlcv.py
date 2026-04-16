"""
Fetch OHLCV data for all active stocks using Upstox.
Reads the stock list from Supabase and pulls daily candles instrument-by-instrument.
"""


import pandas as pd
import time

from services.ml.config import get_supabase
from services.api.services.market_data import fetch_historical_daily


def get_stock_list() -> pd.DataFrame:
    """Read all stocks from Supabase stocks table."""
    sb = get_supabase()
    resp = sb.table("stocks").select("symbol, yf_ticker, company_name").execute()
    return pd.DataFrame(resp.data)


def fetch_ohlcv(days: int = 365) -> pd.DataFrame:
    """
    Fetch OHLCV data for all active stocks using Upstox.

    Args:
        days: Number of historical days to fetch (default 365).

    Returns:
        DataFrame with columns: symbol, date, open, high, low, close, volume
    """
    stocks = get_stock_list()
    if stocks.empty:
        print("No stocks found in database.")
        return pd.DataFrame()

    rows = []
    for _, row in stocks.iterrows():
        symbol = row["symbol"]
        try:
            candles = fetch_historical_daily(symbol, row.get("yf_ticker"), days)
            for r in candles:
                rows.append({
                    "symbol": symbol,
                    "date": r["date"],
                    "open": round(float(r["open"]), 2),
                    "high": round(float(r["high"]), 2),
                    "low": round(float(r["low"]), 2),
                    "close": round(float(r["close"]), 2),
                    "volume": int(r["volume"]),
                })
            print(f"Fetched {len(candles)} rows for {symbol}")
            time.sleep(0.25)
        except Exception as e:
            print(f"  Warning: failed to fetch {symbol}: {e}")

    df = pd.DataFrame(rows)
    print(f"Fetched {len(df)} OHLCV rows for {df['symbol'].nunique()} stocks.")
    return df


if __name__ == "__main__":
    df = fetch_ohlcv()
    print(df.head())
    print(df.dtypes)
