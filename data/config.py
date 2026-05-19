import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_session():
    """Return a new SQLAlchemy session for pipeline use."""
    from backend.database import SessionLocal
    return SessionLocal()
