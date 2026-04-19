# NiveshSutra

NiveshSutra is an AI-assisted Indian equity analysis and portfolio management platform for NSE-listed stocks. It combines technical indicators, financial-news sentiment, momentum scoring, and portfolio optimization into a single workflow backed by Supabase.

The repo is Streamlit-first for the product UI. FastAPI, Python ML jobs, and Supabase support ingestion, scoring, and automation.

## What It Does

- Ingests OHLCV market data for tracked Indian equities
- Computes indicators such as RSI, MACD, Bollinger Bands, SMA, EMA, ATR, and OBV
- Pulls Moneycontrol news and scores headlines with FinBERT
- Generates explainable buy/hold/sell signals from technical, sentiment, and momentum inputs
- Tracks holdings, watchlists, alerts, and personalized risk profiles
- Runs mean-variance portfolio optimization based on user risk tolerance

## Tech Stack

| Layer | Technology |
|-------|------------|
| Product UI | Streamlit |
| Charts | Plotly |
| API | FastAPI |
| Language | Python 3.12 |
| Database/Auth | Supabase (Postgres, Auth, RLS) |
| Market data | yfinance, Moneycontrol market scraping |
| News | Moneycontrol via `moneycontrol-api` |
| Technical analysis | pandas, pandas-ta |
| Sentiment | Hugging Face Transformers, ProsusAI/finbert, PyTorch |
| Portfolio optimization | PyPortfolioOpt, SciPy, scikit-learn |
| Notifications | Resend |

## Current Architecture

```text
Public product UI
  -> Streamlit app
  -> Supabase Auth + database reads/writes
  -> shared Python helpers
  -> FastAPI service URL for stock onboarding and portfolio optimization

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
|   |-- config.py               Hosted/local config resolution
|   |-- supabase_client.py      Supabase client factories
|   |-- utils.py                Formatting and personalization helpers
|   `-- pages/
|-- services/
|   |-- api/                    FastAPI backend
|   |-- ml/                     Ingestion, sentiment, signals, optimizer, alerts
|   `-- notifications/          Email notification service
|-- scripts/                    Seed and orchestration scripts
|-- supabase/migrations/        Database schema and RLS migrations
|-- docs/                       Architecture and notes
|-- .streamlit/                 Streamlit local config and secrets example
|-- render.yaml                 Render deployment blueprint for FastAPI
|-- requirements.txt
`-- .env.example
```

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

The root `requirements.txt` is intentionally frontend-only for Streamlit hosting.
Install backend and ML dependencies separately when needed:

```bash
pip install -r services/api/requirements.txt
pip install -r services/ml/requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values.

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
MARKET_DATA_CACHE_TTL_SECONDS=60
PUBLIC_APP_URL=https://your-streamlit-app-url
API_BASE_URL=https://your-render-api-url
FASTAPI_PORT=8000
ENVIRONMENT=development

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

### 5. Run the Streamlit app

```bash
streamlit run streamlit_app/app.py
```

The Streamlit app is the primary local product surface.

### 6. Run the API separately if needed

```bash
python -m uvicorn services.api.main:app --reload --port 8000
```

## Deployment

### Streamlit frontend

Deploy the public product UI from `streamlit_app/app.py` to Streamlit Community Cloud.

- App file: `streamlit_app/app.py`
- Python version: use the repo `.python-version`
- Dependencies: install from the repo root `requirements.txt`
- Secrets: copy values from `.streamlit/secrets.toml.example` into the Streamlit Cloud secrets manager

Recommended frontend secrets:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `API_BASE_URL` if you later wire Streamlit pages to the FastAPI service
- `PUBLIC_APP_URL`

### FastAPI backend

Deploy the backend separately to Render using `render.yaml`.

- Build command: `pip install -r services/api/requirements.txt`
- Start command: `uvicorn services.api.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/v1/health`

Recommended backend environment variables:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PUBLIC_APP_URL`
- `MARKET_DATA_CACHE_TTL_SECONDS`
- `ENVIRONMENT=production`

The backend root URL now serves a small landing page with links to the frontend, API docs, and health endpoint instead of returning a raw 404 JSON payload.

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
- The repo now reflects the free-data stack: `yfinance` plus Moneycontrol-based sources.
- The recommended production hosting model is Streamlit Community Cloud for the UI and Render for FastAPI.
- The Streamlit frontend now uses `API_BASE_URL` for stock onboarding and portfolio optimization instead of importing backend modules directly.

## Disclaimer

This project is for educational and portfolio purposes. It is not financial advice.

## License

MIT
