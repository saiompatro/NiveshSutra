import requests
import pandas as pd
import os

BASE_URL = "https://www.alphavantage.co/query"


def fetch_alpha_vantage_daily(symbol: str, outputsize: str = "full") -> pd.DataFrame:
    """
    Fetch daily OHLCV data for a given symbol from Alpha Vantage.
    Returns a DataFrame with columns: date, open, high, low, close, volume
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY is not configured")

    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": api_key,
        "datatype": "json"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if "Time Series (Daily)" not in data:
        raise ValueError(f"Alpha Vantage error for {symbol}: {data.get('Note') or data}")
    ts = data["Time Series (Daily)"]
    rows = []
    for date, values in ts.items():
        rows.append({
            "date": date,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "adj_close": float(values["5. adjusted close"]),
            "volume": int(values["6. volume"]),
        })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df
