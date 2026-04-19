# NiveshSutra Architecture

## System Overview

```mermaid
graph TB
    subgraph Frontend
        A[Next.js 15 App] --> B[Supabase Auth]
        A --> C[FastAPI Backend]
    end

    subgraph Backend
        C --> D[Supabase Postgres]
        C --> E[Auth Middleware]
    end

    subgraph ML Pipeline
        F[Daily Orchestrator] --> G[OHLCV Ingestion]
        F --> H[Sentiment Pipeline]
        F --> I[Signal Engine]
        F --> J[Alert Generator]
        G --> K[yfinance API]
        G --> L[pandas-ta Indicators]
        H --> M[Moneycontrol News API]
        H --> N[FinBERT Model]
        I --> O[Technical Scorer]
        I --> P[Momentum Scorer]
        I --> Q[Weighted Combiner]
    end

    G --> D
    H --> D
    I --> D
    J --> D
```

## Data Flow

1. **Ingestion**: yfinance → OHLCV table → pandas-ta → technical_indicators table
2. **Sentiment**: Moneycontrol news → ticker mapping → FinBERT scoring → sentiment_daily table
3. **Signals**: indicators + sentiment + momentum → weighted combination → signals table
4. **Portfolio**: User holdings + OHLCV returns → PyPortfolioOpt → allocation recommendations

## Signal Engine

```
composite_score = 0.4 × technical_score + 0.3 × sentiment_score + 0.3 × momentum_score

technical_score = 0.3×RSI + 0.3×MACD + 0.2×BB + 0.2×OBV  (each normalized -1 to +1)
momentum_score = mean(5d_return, 20d_return, SMA_crossover)  (each normalized -1 to +1)
sentiment_score = avg(positive_prob - negative_prob)  (from daily aggregation, -1 to +1)

Signal mapping:
  composite >= 0.5  → strong_buy
  composite >= 0.2  → buy
  composite >= -0.2 → hold
  composite >= -0.5 → sell
  composite < -0.5  → strong_sell

confidence = min(|composite| × 2, 1.0)
```

## Database Schema

| Table | Purpose | RLS |
|-------|---------|-----|
| profiles | User profiles + risk scoring | user=own |
| stocks | Nifty 50 master list | public read |
| watchlist | User stock watchlists | user=own |
| holdings | User portfolio holdings | user=own |
| ohlcv | Historical price data | public read |
| technical_indicators | Computed indicators | public read |
| news_articles | Fetched news articles | public read |
| article_sentiments | Per-article FinBERT scores | public read |
| sentiment_daily | Aggregated daily sentiment | public read |
| signal_config | Signal weight configuration | public read |
| signals | Computed buy/sell signals | public read |
| portfolio_optimizations | User optimization runs | user=own |
| optimization_allocations | Recommended allocations | user=own |
| rebalance_history | Rebalancing audit trail | user=own |
| alerts | User notifications | user=own |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Charts | Lightweight Charts (TradingView), Recharts |
| Backend | FastAPI, Python 3.14 |
| Database | Supabase (Postgres 17) |
| Auth | Supabase Auth (email/password) |
| Market Data | yfinance + Moneycontrol market scrape fallback |
| Indicators | pandas-ta (RSI, MACD, BB, SMA, EMA, ATR, OBV) |
| Sentiment | ProsusAI/finbert (HuggingFace) |
| News | Moneycontrol via `moneycontrol-api` |
| Optimization | PyPortfolioOpt (Mean-Variance, CAPM, Ledoit-Wolf) |
