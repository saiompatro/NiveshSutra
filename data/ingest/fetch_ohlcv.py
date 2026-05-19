"""
Fetch OHLCV data for all active stocks using yfinance-backed market data helpers.
Reads the stock list from the local SQLite database and pulls daily candles
instrument-by-instrument.
"""


import pandas as pd
import time

from backend.database import SessionLocal
from backend.models.db_models import Stock
from backend.services.market_data import fetch_historical_daily


def get_stock_list() -> pd.DataFrame:
    """Read all stocks from the local stocks table."""
    session = SessionLocal()
    try:
        rows = session.query(Stock.symbol, Stock.yf_ticker, Stock.company_name).all()
        return pd.DataFrame([{"symbol": r.symbol, "yf_ticker": r.yf_ticker, "company_name": r.company_name} for r in rows])
    finally:
        session.close()


def fetch_ohlcv(days: int = 365) -> pd.DataFrame:
    """
    Fetch OHLCV data for all active stocks using free market data providers.

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
    failed: list[str] = []

    for _, row in stocks.iterrows():
        symbol = row["symbol"]
        try:
            candles = fetch_historical_daily(symbol, row.get("yf_ticker"), days)
            if not candles:
                print(f"  [WARN] No candles returned for {symbol}")
                failed.append(symbol)
            else:
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
                print(f"  [OK]   {symbol}: {len(candles)} rows")
            time.sleep(0.5)
        except Exception as e:
            print(f"  [FAIL] {symbol}: {e}")
            failed.append(symbol)
            time.sleep(0.5)

    if failed:
        print(f"\nFailed symbols ({len(failed)}): {', '.join(failed)}")

    df = pd.DataFrame(rows)
    if not df.empty:
        print(f"\nFetched {len(df)} OHLCV rows for {df['symbol'].nunique()}/{len(stocks)} stocks.")
    return df


if __name__ == "__main__":
    df = fetch_ohlcv()
    print(df.head())
    print(df.dtypes)
