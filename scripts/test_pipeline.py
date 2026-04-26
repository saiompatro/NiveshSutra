"""
Smoke test: fetch OHLCV for 3 symbols and print results.
Run from the project root to verify the data pipeline is functional.

Usage:
    python scripts/test_pipeline.py
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

TEST_SYMBOLS = [
    ("RELIANCE", "RELIANCE.NS"),
    ("INFY", "INFY.NS"),
    ("TCS", "TCS.NS"),
]


def main():
    from backend.services.market_data import fetch_historical_daily, fetch_live_quote

    print("=" * 60)
    print("NiveshSutra — Pipeline Smoke Test")
    print("=" * 60)

    all_passed = True

    for symbol, yf_ticker in TEST_SYMBOLS:
        print(f"\n[{symbol}]")
        try:
            # Historical OHLCV
            t0 = time.time()
            candles = fetch_historical_daily(symbol, yf_ticker, days=5)
            elapsed = time.time() - t0
            if candles:
                latest = candles[-1]
                print(f"  historical : {len(candles)} rows  latest={latest['date']}  close={latest['close']}  ({elapsed:.1f}s)")
            else:
                print(f"  historical : [FAIL] no candles returned ({elapsed:.1f}s)")
                all_passed = False

            # Live quote
            t0 = time.time()
            quote = fetch_live_quote(symbol, yf_ticker)
            elapsed = time.time() - t0
            print(f"  live quote : price={quote.price}  chg={quote.change:+.2f}  day={quote.latest_trading_day}  via={quote.provider}  ({elapsed:.1f}s)")

        except Exception as e:
            print(f"  [ERROR] {e}")
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("RESULT: PASS — pipeline is functional")
    else:
        print("RESULT: FAIL — check errors above")
    print("=" * 60)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
