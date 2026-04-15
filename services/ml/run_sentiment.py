"""
CLI entry point: run the full sentiment analysis pipeline.

Usage:
    python -m services.ml.run_sentiment
"""


def main():
    from services.ml.sentiment import run_sentiment_pipeline

    run_sentiment_pipeline()


if __name__ == "__main__":
    main()
