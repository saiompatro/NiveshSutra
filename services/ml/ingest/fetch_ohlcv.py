"""
Fetch OHLCV data for all Nifty 50 stocks using yfinance.
Reads the stock list from Supabase and downloads data in batch.
"""


import pandas as pd
import time
from services.ml.ingest.alpha_vantage_utils import fetch_alpha_vantage_daily

from services.ml.config import get_supabase


def get_stock_list() -> pd.DataFrame:
    """Read all stocks from Supabase stocks table."""
    sb = get_supabase()
    resp = sb.table("stocks").select("symbol, yf_ticker, company_name").execute()
    return pd.DataFrame(resp.data)


def fetch_ohlcv(days: int = 365) -> pd.DataFrame:
    """
    Fetch OHLCV data for all Nifty 50 stocks using Alpha Vantage.

    Args:
        days: Number of historical days to fetch (default 365).

    Returns:
        DataFrame with columns: symbol, date, open, high, low, close, adj_close, volume
    """
    stocks = get_stock_list()
    if stocks.empty:
        print("No stocks found in database.")
        return pd.DataFrame()

    rows = []
    for _, row in stocks.iterrows():
        symbol = row["symbol"]
        # Alpha Vantage uses NSE: {symbol}.NS
        av_symbol = f"{symbol}.NS"
        try:
            df = fetch_alpha_vantage_daily(av_symbol)
            # Only keep last N days
            df = df.sort_values("date").tail(days)
            for _, r in df.iterrows():
                rows.append({
                    "symbol": symbol,
                    "date": r["date"].strftime("%Y-%m-%d"),
                    "open": round(float(r["open"]), 2),
                    "high": round(float(r["high"]), 2),
                    "low": round(float(r["low"]), 2),
                    "close": round(float(r["close"]), 2),
                    "adj_close": round(float(r["adj_close"]), 2),
                    "volume": int(r["volume"]),
                })
            print(f"Fetched {len(df)} rows for {symbol}")
            time.sleep(12)  # Alpha Vantage free API: 5 requests/minute
        except Exception as e:
            print(f"  Warning: failed to fetch {symbol}: {e}")

    df = pd.DataFrame(rows)
    print(f"Fetched {len(df)} OHLCV rows for {df['symbol'].nunique()} stocks.")
    return df


if __name__ == "__main__":
    df = fetch_ohlcv()
    print(df.head())
    print(df.dtypes)
