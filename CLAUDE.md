# NiveshSutra

AI-powered Indian equity wealth management platform combining technical analysis, NLP sentiment, and portfolio optimization.

## Project Structure
- `streamlit_app/` — Streamlit frontend (Python)
  - `app.py` — Entry point: auth gate (login/signup) + onboarding wizard
  - `auth.py` — Supabase auth helpers (login, signup, logout, session state)
  - `supabase_client.py` — Client factory (anon, authed-with-JWT, admin)
  - `utils.py` — Formatting, signal colors, personalization logic
  - `pages/` — Multi-page Streamlit app
    - `1_Dashboard.py` — Portfolio metrics, Nifty 50, sentiment, signals, watchlist, alerts
    - `2_Stocks.py` — Stock browser with search/filter and add-stock
    - `3_Stock_Detail.py` — Candlestick chart, technical indicators, sentiment timeline
    - `4_Signals.py` — Signal table with risk-profile personalization and accept/track
    - `5_Portfolio.py` — Holdings, P&L, allocation pie, MVO optimization
    - `6_Settings.py` — Profile, risk re-assessment, notification preferences
- `services/api/` — FastAPI backend (unchanged)
- `services/ml/` — ML pipelines: ingest, sentiment, signals, optimizer (unchanged)
- `supabase/migrations/` — Database migrations (already applied)
- `scripts/` — Seed data, daily pipeline orchestrator
- `docs/` — Architecture, research notes

## Commands
```bash
# Activate venv first (Windows)
.venv/Scripts/activate

# Frontend (Streamlit)
streamlit run streamlit_app/app.py

# Backend API (optional — Streamlit imports Python modules directly)
cd services/api && python -m uvicorn services.api.main:app --reload --port 8000

# Data ingestion (fetches OHLCV + computes indicators)
python -m services.ml.run_ingest --days 365

# Sentiment pipeline
python -m services.ml.run_sentiment

# Signal computation
python -m services.ml.run_signals

# Full daily pipeline
python scripts/run_daily_pipeline.py
```

## Conventions
- Auth: Supabase Auth — session stored in `st.session_state["session"]`
- RLS: use `get_authed_client(access_token)` for user-specific tables
- Stock symbols in DB without `.NS` suffix; `.NS` appended for yfinance
- All monetary values in INR
- Charts: Plotly (`go.Candlestick`, `go.Pie`, `go.Scatter`)
- Signal personalization logic lives in `utils.py`
- Market data accessed by importing `services.api.services.market_data` directly

## Environment
- Copy `.env.example` to `.env` and fill in Supabase credentials
- Python venv: `python -m venv .venv`
- Install deps: `pip install -r requirements.txt`

## Database
- Supabase Postgres 17 (ap-south-1)
- 8 migrations applied (001–008)
- RLS enabled on all tables
- Auto-profile creation on signup via trigger
