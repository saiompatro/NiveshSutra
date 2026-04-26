"""
CLI entry point: run the hybrid signal computation pipeline.

Usage:
    python -m data.run_signals
"""


def main():
    from data.signals import run_signals_pipeline

    run_signals_pipeline()


if __name__ == "__main__":
    main()
