# NiveshSutra

NiveshSutra is an AI-assisted Indian equity analysis and portfolio management platform for NSE-listed stocks. It combines technical indicators, financial-news sentiment, momentum scoring, and portfolio optimization into a single workflow backed by Supabase.

The current repo is Streamlit-first for the product UI, with FastAPI routes and Python ML/data pipelines supporting ingestion, scoring, and automation.

## What It Does

- Ingests OHLCV market data for tracked Indian equities
- Computes technical indicators such as RSI, MACD, Bollinger Bands, SMA, EMA, ATR, and OBV
- Pulls Moneycontrol news and scores headlines with FinBERT
- Generates explainable buy/hold/sell signals from technical, sentiment, and momentum inputs
- Tracks holdings, watchlists, alerts, and personalized risk profiles
- Runs mean-variance portfolio optimization for users based on their risk tolerance

## Signal Engine

```text
composite = 0.4 * technical + 0.3 * sentiment + 0.3 * momentum

technical = weighted score from RSI, MACD, Bollinger Bands, and OBV
momentum  = score from short and medium term price behavior
sentiment = average(FinBERT positive - negative)

Signal mapping:
>= 0.5   -> strong_buy
>= 0.2   -> buy
>= -0.2  -> hold
>= -0.5  -> sell
< -0.5   -> strong_sell
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Product UI | Streamlit |
| Charts | Plotly |
| API | FastAPI |
| Language | Python |
| Database/Auth | Supabase (Postgres, Auth, RLS) |
| Market data | yfinance, Moneycontrol market scraping |
| News | Moneycontrol via `moneycontrol-api` |
| Technical analysis | pandas, pandas-ta |
| Sentiment | Hugging Face Transformers, ProsusAI/finbert, PyTorch |
| Portfolio optimization | PyPortfolioOpt, SciPy, scikit-learn |
| Notifications | Resend |

## Current Architecture

```text
Streamlit app
  -> Supabase Auth + database reads/writes
  -> shared Python service layer

FastAPI API
  -> authenticated REST endpoints for stocks, holdings, watchlist,
     signals, sentiment, portfolio, alerts, and notifications

ML/Data pipelines
  -> ingest OHLCV
  -> compute indicators
  -> fetch and score news sentiment
  -> generate signals
  -> generate alerts
```

## Project Structure

```text
NiveshSutra/
|-- streamlit_app/              Streamlit frontend
|   |-- app.py                  Entry point
|   |-- auth.py                 Login/signup/session helpers
|   |-- supabase_client.py      Supabase client factories
|   |-- utils.py                Formatting and personalization helpers
|   `-- pages/
|       |-- 1_Dashboard.py
|       |-- 2_Stocks.py
|       |-- 3_Stock_Detail.py
|       |-- 4_Signals.py
|       |-- 5_Portfolio.py
|       `-- 6_Settings.py
|-- services/
|   |-- api/                    FastAPI backend
|   |-- ml/                     Ingestion, sentiment, signals, optimizer, alerts
|   `-- notifications/          Email notification service
|-- scripts/                    Seed and orchestration scripts
|-- supabase/migrations/        Database schema and RLS migrations
|-- docs/                       Architecture and notes
|-- requirements.txt
`-- .env.example
```

## Core Features

- Risk-profiled onboarding with conservative, moderate, and aggressive segmentation
- Dashboard with portfolio summary, market overview, sentiment, watchlist, and alerts
- Stock explorer with live quote context, OHLCV history, indicators, and article sentiment
- Signal engine with explainable recommendations
- Portfolio holdings tracker with PnL and allocation views
- Portfolio optimization based on user risk profile
- Signal tracking and email notifications
- Background daily pipeline for ingestion, scoring, and alert generation

## Setup

### Prerequisites

- Python 3.12 recommended
- A Supabase project
- Optional: Resend account for email notifications

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/NiveshSutra.git
cd NiveshSutra

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values.

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
MARKET_DATA_CACHE_TTL_SECONDS=60
FASTAPI_PORT=8000
ENVIRONMENT=development

# Optional email notifications
RESEND_API_KEY=re_your_resend_api_key
RESEND_FROM_EMAIL=NiveshSutra <noreply@niveshsutra.com>
```

### 3. Apply database migrations

Apply the migrations in `supabase/migrations/` in order:

1. `001_foundation.sql`
2. `002_market_data.sql`
3. `003_sentiment.sql`
4. `004_signals.sql`
5. `005_portfolio_optimization.sql`
6. `006_alerts.sql`
7. `007_signal_tracking_and_notifications.sql`
8. `008_allow_authenticated_stock_inserts.sql`

### 4. Seed the stock universe

```bash
python scripts/seed_nifty50.py
```

### 5. Run the app

```bash
streamlit run streamlit_app/app.py
```

The Streamlit app is the primary local product surface.

### 6. Run the API separately if needed

```bash
cd services/api
python -m uvicorn services.api.main:app --reload --port 8000
```

## Data Pipeline

Run the full daily pipeline:

```bash
python scripts/run_daily_pipeline.py
```

Run individual stages:

```bash
python -m services.ml.run_ingest --days 365
python -m services.ml.run_sentiment
python -m services.ml.run_signals
```

Notes:

- The first FinBERT run downloads the model weights locally.
- Market data is sourced from free providers only.
- News ingestion currently uses Moneycontrol via `moneycontrol-api`.

## API Surface

The FastAPI app exposes routes under `/api/v1` for:

- health
- profile
- stock search
- stocks and market data
- watchlist
- holdings
- sentiment
- signals
- portfolio
- alerts
- notifications

See [docs/architecture.md](docs/architecture.md) for higher-level system notes.

## Status Notes

- Streamlit is the active frontend in this repository.
- The README now reflects the current free-data stack: `yfinance` plus Moneycontrol-based sources.
- Older references to Next.js and paid market-data providers are no longer part of the active setup.

## Disclaimer

This project is for educational and portfolio purposes. It is not financial advice.

## License

MIT
