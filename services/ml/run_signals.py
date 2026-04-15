"""
CLI entry point: run the hybrid signal computation pipeline.

Usage:
    python -m services.ml.run_signals
"""


def main():
    from services.ml.signals import run_signals_pipeline

    run_signals_pipeline()


if __name__ == "__main__":
    main()
