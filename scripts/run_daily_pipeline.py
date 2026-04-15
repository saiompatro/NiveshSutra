"""
Daily pipeline orchestrator.

Runs the full NiveshSutra ML pipeline in order:
  1. Ingest OHLCV + compute indicators
  2. Sentiment pipeline (RSS -> FinBERT -> aggregate)
  3. Signal computation (technical + sentiment + momentum -> composite)
  4. Alert generation (signal changes, sentiment shifts, portfolio drift)

Usage:
    python scripts/run_daily_pipeline.py
    python scripts/run_daily_pipeline.py --days 90
"""

import argparse
import sys
import time
from datetime import datetime, timezone

# Ensure project root is on sys.path so services.ml imports work
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(description="Run the full daily ML pipeline")
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of historical days to fetch for OHLCV (default: 365)",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip OHLCV ingestion step",
    )
    parser.add_argument(
        "--skip-sentiment",
        action="store_true",
        help="Skip sentiment pipeline step",
    )
    parser.add_argument(
        "--skip-signals",
        action="store_true",
        help="Skip signal computation step",
    )
    parser.add_argument(
        "--skip-alerts",
        action="store_true",
        help="Skip alert generation step",
    )
    args = parser.parse_args()

    overall_start = time.time()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print("#" * 60)
    print(f"# NiveshSutra Daily Pipeline - {now}")
    print("#" * 60)

    # ------------------------------------------------------------------
    # Step 1: Ingest OHLCV + indicators
    # ------------------------------------------------------------------
    if not args.skip_ingest:
        print()
        print("=" * 60)
        print("PIPELINE STEP 1/4: OHLCV Ingestion + Indicators")
        print("=" * 60)
        try:
            from services.ml.run_ingest import main as run_ingest

            # Override sys.argv so argparse inside run_ingest works
            saved_argv = sys.argv
            sys.argv = ["run_ingest", "--days", str(args.days)]
            run_ingest()
            sys.argv = saved_argv
        except Exception as exc:
            print(f"ERROR in ingestion step: {exc}")
            import traceback

            traceback.print_exc()
    else:
        print("\n[SKIPPED] OHLCV Ingestion")

    # ------------------------------------------------------------------
    # Step 2: Sentiment pipeline
    # ------------------------------------------------------------------
    if not args.skip_sentiment:
        print()
        print("=" * 60)
        print("PIPELINE STEP 2/4: Sentiment Analysis")
        print("=" * 60)
        try:
            from services.ml.sentiment import run_sentiment_pipeline

            run_sentiment_pipeline()
        except Exception as exc:
            print(f"ERROR in sentiment step: {exc}")
            import traceback

            traceback.print_exc()
    else:
        print("\n[SKIPPED] Sentiment Analysis")

    # ------------------------------------------------------------------
    # Step 3: Signal computation
    # ------------------------------------------------------------------
    if not args.skip_signals:
        print()
        print("=" * 60)
        print("PIPELINE STEP 3/4: Signal Computation")
        print("=" * 60)
        try:
            from services.ml.signals import run_signals_pipeline

            run_signals_pipeline()
        except Exception as exc:
            print(f"ERROR in signals step: {exc}")
            import traceback

            traceback.print_exc()
    else:
        print("\n[SKIPPED] Signal Computation")

    # ------------------------------------------------------------------
    # Step 4: Alert generation
    # ------------------------------------------------------------------
    if not args.skip_alerts:
        print()
        print("=" * 60)
        print("PIPELINE STEP 4/4: Alert Generation")
        print("=" * 60)
        try:
            from services.ml.alerts import generate_alerts

            generate_alerts()
        except Exception as exc:
            print(f"ERROR in alerts step: {exc}")
            import traceback

            traceback.print_exc()
    else:
        print("\n[SKIPPED] Alert Generation")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    total_elapsed = time.time() - overall_start
    print()
    print("#" * 60)
    print(f"# DAILY PIPELINE COMPLETE in {total_elapsed:.1f}s")
    print("#" * 60)


if __name__ == "__main__":
    main()
