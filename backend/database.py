"""Local SQLite database via SQLAlchemy."""

import os
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_db_path = (PROJECT_ROOT / "niveshsutra.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_EMAIL = "local@niveshsutra.local"


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, connection_record):
    if "sqlite" in DATABASE_URL:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def get_db():
    """FastAPI dependency -- yields a session then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and seed the default local user."""
    import backend.models.db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _seed_default_user()


def _seed_default_user():
    from backend.models.db_models import Profile, SignalConfig
    db = SessionLocal()
    try:
        if not db.query(Profile).filter_by(id=DEFAULT_USER_ID).first():
            db.add(Profile(
                id=DEFAULT_USER_ID,
                email=DEFAULT_USER_EMAIL,
                full_name="Local User",
                onboarding_complete=True,
                risk_profile="moderate",
                risk_score=10,
            ))
        if not db.query(SignalConfig).filter_by(name="default").first():
            db.add(SignalConfig(
                name="default",
                technical_weight=0.4,
                sentiment_weight=0.3,
                momentum_weight=0.3,
                is_active=True,
            ))
        db.commit()
    finally:
        db.close()


def row_to_dict(obj, rels=None):
    """Convert a SQLAlchemy model instance to a JSON-friendly dict."""
    if obj is None:
        return None
    d = {}
    for c in obj.__table__.columns:
        v = getattr(obj, c.name)
        if isinstance(v, datetime):
            d[c.name] = v.isoformat()
        elif isinstance(v, date):
            d[c.name] = str(v)
        elif isinstance(v, Decimal):
            d[c.name] = float(v)
        else:
            d[c.name] = v
    if rels:
        for r in rels:
            rel_obj = getattr(obj, r, None)
            if rel_obj is None:
                d[r] = None
            elif isinstance(rel_obj, list):
                d[r] = [row_to_dict(item) for item in rel_obj]
            else:
                d[r] = row_to_dict(rel_obj)
    return d
