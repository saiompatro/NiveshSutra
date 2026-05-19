"""SQLAlchemy ORM models for NiveshSutra."""

from uuid import uuid4
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float,
    ForeignKey, Index, Integer, String, BigInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid():
    return str(uuid4())


# ── users / profiles ────────────────────────────────────────────────

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    full_name = Column(String)
    risk_profile = Column(String)            # conservative | moderate | aggressive
    risk_score = Column(Integer)
    onboarding_complete = Column(Boolean, default=False)
    volatility_tolerance = Column(Integer)
    time_horizon_score = Column(Integer)
    knowledge_score = Column(Integer)
    investable_surplus_range = Column(String)
    email_notifications_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    watchlist_items = relationship("Watchlist", back_populates="profile")
    holdings = relationship("Holding", back_populates="profile")
    alerts = relationship("Alert", back_populates="profile")


# ── stocks ───────────────────────────────────────────────────────────

class Stock(Base):
    __tablename__ = "stocks"

    symbol = Column(String, primary_key=True)
    yf_ticker = Column(String, nullable=False, unique=True)
    company_name = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    industry = Column(String)
    market_cap_category = Column(String)     # large | mid | small
    is_nifty50 = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── watchlist ────────────────────────────────────────────────────────

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "symbol"),)

    profile = relationship("Profile", back_populates="watchlist_items")
    stock = relationship("Stock")


# ── holdings ─────────────────────────────────────────────────────────

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    buy_date = Column(String, nullable=False)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("Profile", back_populates="holdings")
    stock = relationship("Stock")


# ── OHLCV ────────────────────────────────────────────────────────────

class Ohlcv(Base):
    __tablename__ = "ohlcv"

    id = Column(String, primary_key=True, default=_uuid)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    date = Column(String, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    adj_close = Column(Float)
    volume = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "date"),
        Index("idx_ohlcv_symbol_date", "symbol", "date"),
    )


# ── technical indicators ─────────────────────────────────────────────

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"

    id = Column(String, primary_key=True, default=_uuid)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    date = Column(String, nullable=False)
    rsi_14 = Column(Float)
    macd_line = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    atr_14 = Column(Float)
    obv = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "date"),
        Index("idx_indicators_symbol_date", "symbol", "date"),
    )


# ── news / sentiment ────────────────────────────────────────────────

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(String, primary_key=True, default=_uuid)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    source = Column(String)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class ArticleSentiment(Base):
    __tablename__ = "article_sentiments"

    id = Column(String, primary_key=True, default=_uuid)
    article_id = Column(String, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    positive_prob = Column(Float)
    negative_prob = Column(Float)
    neutral_prob = Column(Float)
    sentiment_label = Column(String)
    relevance_score = Column(Float, default=1.0)
    computed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("article_id", "symbol"),)

    article = relationship("NewsArticle")


class SentimentDaily(Base):
    __tablename__ = "sentiment_daily"

    id = Column(String, primary_key=True, default=_uuid)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    date = Column(String, nullable=False)
    avg_sentiment = Column(Float)
    positive_avg = Column(Float)
    negative_avg = Column(Float)
    neutral_avg = Column(Float)
    article_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "date"),
        Index("idx_sentiment_daily_symbol_date", "symbol", "date"),
    )


# ── signals ──────────────────────────────────────────────────────────

class SignalConfig(Base):
    __tablename__ = "signal_config"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False, unique=True)
    technical_weight = Column(Float, default=0.4)
    sentiment_weight = Column(Float, default=0.3)
    momentum_weight = Column(Float, default=0.3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=_uuid)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    date = Column(String, nullable=False)
    technical_score = Column(Float)
    sentiment_score = Column(Float)
    momentum_score = Column(Float)
    composite_score = Column(Float)
    signal = Column(String)                  # strong_buy|buy|hold|sell|strong_sell
    confidence = Column(Float)
    explanation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("symbol", "date"),
        Index("idx_signals_symbol_date", "symbol", "date"),
        Index("idx_signals_signal", "signal"),
    )


# ── portfolio optimization ───────────────────────────────────────────

class PortfolioOptimization(Base):
    __tablename__ = "portfolio_optimizations"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    risk_profile = Column(String)
    optimization_method = Column(String)
    target_return = Column(Float)
    target_risk = Column(Float)
    expected_return = Column(Float)
    expected_risk = Column(Float)
    sharpe_ratio = Column(Float)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    allocations = relationship("OptimizationAllocation", back_populates="optimization")


class OptimizationAllocation(Base):
    __tablename__ = "optimization_allocations"

    id = Column(String, primary_key=True, default=_uuid)
    optimization_id = Column(String, ForeignKey("portfolio_optimizations.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    current_weight = Column(Float)
    recommended_weight = Column(Float)
    current_value = Column(Float)
    recommended_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    optimization = relationship("PortfolioOptimization", back_populates="allocations")


class RebalanceHistory(Base):
    __tablename__ = "rebalance_history"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    optimization_id = Column(String, ForeignKey("portfolio_optimizations.id"), nullable=True)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    action = Column(String)                  # buy | sell | hold
    quantity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── alerts ───────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String, nullable=False)   # signal_change|sentiment_shift|rebalance_drift|price_alert
    title = Column(String, nullable=False)
    message = Column(String)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_alerts_user_unread", "user_id", "is_read"),
    )

    profile = relationship("Profile", back_populates="alerts")


# ── signal tracking ──────────────────────────────────────────────────

class AcceptedSignal(Base):
    __tablename__ = "accepted_signals"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    signal_type = Column(String, nullable=False)
    signal_date = Column(String, nullable=False)
    composite_score = Column(Float)
    status = Column(String, default="active")   # active | executed | cancelled
    accepted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_accepted_signals_user", "user_id", "status"),
        Index("idx_accepted_signals_symbol", "symbol"),
    )


class SignalNotification(Base):
    __tablename__ = "signal_notifications"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    last_signal = Column(String)
    last_notified_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "symbol"),
        Index("idx_signal_notifications_active", "user_id", "is_active"),
    )
