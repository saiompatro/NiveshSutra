"""
CLI entry point: orchestrates OHLCV fetch -> compute indicators -> store in Supabase.
"""

import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="Ingest OHLCV data and compute technical indicators")
    parser.add_argument("--days", type=int, default=365, help="Number of historical days to fetch (default: 365)")
    args = parser.parse_args()

    start = time.time()

    # Step 1: Fetch OHLCV
    print("=" * 60)
    print("STEP 1: Fetching OHLCV data")
    print("=" * 60)
    from services.ml.ingest.fetch_ohlcv import fetch_ohlcv

    ohlcv_df = fetch_ohlcv(days=args.days)
    if ohlcv_df.empty:
        print("No OHLCV data fetched. Exiting.")
        sys.exit(1)

    # Step 2: Compute indicators
    print()
    print("=" * 60)
    print("STEP 2: Computing technical indicators")
    print("=" * 60)
    from services.ml.ingest.compute_indicators import compute_indicators

    indicators_df = compute_indicators(ohlcv_df)

    # Step 3: Store in Supabase
    print()
    print("=" * 60)
    print("STEP 3: Storing data in Supabase")
    print("=" * 60)
    from services.ml.ingest.store import upsert_ohlcv, upsert_indicators

    ohlcv_count = upsert_ohlcv(ohlcv_df)
    indicator_count = upsert_indicators(indicators_df)

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"DONE in {elapsed:.1f}s")
    print(f"  OHLCV rows:     {ohlcv_count}")
    print(f"  Indicator rows:  {indicator_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
