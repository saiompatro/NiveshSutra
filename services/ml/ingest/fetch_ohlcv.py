"""
Fetch OHLCV data for all Nifty 50 stocks using yfinance.
Reads the stock list from Supabase and downloads data in batch.
"""

import datetime
import pandas as pd
import yfinance as yf

from services.ml.config import get_supabase


def get_stock_list() -> pd.DataFrame:
    """Read all stocks from Supabase stocks table."""
    sb = get_supabase()
    resp = sb.table("stocks").select("symbol, yf_ticker, company_name").execute()
    return pd.DataFrame(resp.data)


def fetch_ohlcv(days: int = 365) -> pd.DataFrame:
    """
    Fetch OHLCV data for all Nifty 50 stocks using yfinance batch download.

    Args:
        days: Number of historical days to fetch (default 365).

    Returns:
        DataFrame with columns: symbol, date, open, high, low, close, adj_close, volume
    """
    stocks = get_stock_list()
    if stocks.empty:
        print("No stocks found in database.")
        return pd.DataFrame()

    # Build ticker list with .NS suffix for yfinance
    ticker_map = dict(zip(stocks["yf_ticker"], stocks["symbol"]))
    tickers = list(ticker_map.keys())

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    print(f"Downloading OHLCV for {len(tickers)} tickers from {start_date} to {end_date}...")
    raw = yf.download(
        tickers=tickers,
        start=str(start_date),
        end=str(end_date),
        group_by="ticker",
        auto_adjust=False,
        threads=True,
    )

    if raw.empty:
        print("No data returned from yfinance.")
        return pd.DataFrame()

    rows = []
    for yf_ticker, symbol in ticker_map.items():
        try:
            if len(tickers) == 1:
                ticker_data = raw.copy()
            else:
                ticker_data = raw[yf_ticker].copy()

            ticker_data = ticker_data.dropna(subset=["Close"])
            if ticker_data.empty:
                continue

            for dt, row in ticker_data.iterrows():
                rows.append({
                    "symbol": symbol,
                    "date": pd.Timestamp(dt).strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2) if pd.notna(row["Open"]) else None,
                    "high": round(float(row["High"]), 2) if pd.notna(row["High"]) else None,
                    "low": round(float(row["Low"]), 2) if pd.notna(row["Low"]) else None,
                    "close": round(float(row["Close"]), 2),
                    "adj_close": round(float(row["Adj Close"]), 2) if pd.notna(row.get("Adj Close", row["Close"])) else round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                })
        except Exception as e:
            print(f"  Warning: failed to process {yf_ticker} ({symbol}): {e}")

    df = pd.DataFrame(rows)
    print(f"Fetched {len(df)} OHLCV rows for {df['symbol'].nunique()} stocks.")
    return df


if __name__ == "__main__":
    df = fetch_ohlcv()
    print(df.head())
    print(df.dtypes)
