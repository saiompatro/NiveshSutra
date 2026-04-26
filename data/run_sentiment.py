"""
CLI entry point: run the full sentiment analysis pipeline.

Usage:
    python -m data.run_sentiment
"""


def main():
    from data.sentiment import run_sentiment_pipeline

    run_sentiment_pipeline()


if __name__ == "__main__":
    main()
