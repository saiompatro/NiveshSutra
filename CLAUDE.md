# NiveshSutra

AI-powered Indian equity wealth management platform combining technical analysis, NLP sentiment, and portfolio optimization.

## Project Structure

```
NiveshSutra/
├── frontend/               # Next.js 14 + Tailwind CSS + shadcn/ui (Phase 3)
├── backend/                # FastAPI REST API
│   ├── main.py             # App factory, CORS, router registration
│   ├── config.py           # Pydantic Settings (env vars)
│   ├── dependencies.py     # Auth + Supabase client DI
│   ├── routers/            # One file per resource
│   ├── services/
│   │   └── market_data.py  # yfinance quote + OHLCV fetching (patched)
│   └── models/             # Pydantic request/response models
├── data/                   # ML + data ingestion layer
│   ├── config.py           # Supabase service-role client
│   ├── ingest/             # OHLCV fetch, indicator compute, Supabase store
│   ├── sentiment/          # Moneycontrol RSS → FinBERT → daily aggregate
│   ├── signals/            # Technical + sentiment + momentum composite
│   └── alerts/             # Signal changes, sentiment shifts, drift checks
├── math_engine/            # Mathematical models (MVO optimizer)
│   └── optimizer/          # PyPortfolioOpt: min_vol / max_sharpe / efficient_return
├── notifications/          # Email service (Resend API)
├── streamlit_app/          # Legacy Streamlit frontend (to be replaced by frontend/)
│   ├── app.py              # Entry point: auth gate + onboarding
│   ├── pages/              # Multi-page Streamlit app (1_Dashboard … 6_Settings)
│   └── ...
├── scripts/
│   ├── run_daily_pipeline.py  # Orchestrates all 4 pipeline steps
│   ├── seed_nifty50.py        # One-time Nifty 50 DB seed
│   └── test_pipeline.py       # Smoke test: fetch 3 symbols, print results
├── supabase/migrations/    # 001–008 (already applied)
├── docs/                   # Architecture, research notes
├── render.yaml             # Render web + cron service definitions
└── requirements.txt        # Streamlit frontend deps
```

## Commands

```bash
# Activate venv first (Windows)
.venv/Scripts/activate

# Smoke test (verify pipeline is working)
python scripts/test_pipeline.py

# Frontend (Streamlit legacy)
streamlit run streamlit_app/app.py

# Backend API
python -m uvicorn backend.main:app --reload --port 8000

# Data ingestion (fetches OHLCV + computes indicators)
python -m data.run_ingest --days 365

# Sentiment pipeline
python -m data.run_sentiment

# Signal computation
python -m data.run_signals

# Full daily pipeline
python scripts/run_daily_pipeline.py
```

## Conventions

- Auth: Supabase Auth — session stored in `st.session_state["session"]`
- RLS: use `get_authed_client(access_token)` for user-specific tables
- Stock symbols in DB without `.NS` suffix; `.NS` appended for yfinance
- All monetary values in INR
- Charts: Plotly (`go.Candlestick`, `go.Pie`, `go.Scatter`)
- Signal personalization logic lives in `streamlit_app/utils.py`
- Market data imported from `backend.services.market_data`
- ML pipeline uses `data.config.get_supabase` (service-role key)

## Environment

- Copy `.env.example` to `.env` and fill in Supabase credentials
- Python venv: `python -m venv .venv`
- Install all deps: `pip install -r requirements.txt && pip install -r backend/requirements.txt`

## Database

- Supabase Postgres 17 (ap-south-1)
- 8 migrations applied (001–008)
- RLS enabled on all tables
- Auto-profile creation on signup via trigger

## Pipeline Schedule (Render cron)

- Runs daily Mon–Fri at 10:15 UTC (15:45 IST) — 15 min after NSE closes
- 4 steps: OHLCV ingest → sentiment → signals → alerts
- Defined in `render.yaml` as `niveshsutra-daily-pipeline`
