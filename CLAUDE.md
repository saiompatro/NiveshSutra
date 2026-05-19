# NiveshSutra

AI-powered Indian equity wealth management platform combining technical analysis, NLP sentiment, and portfolio optimization.

## Project Structure

```
NiveshSutra/
├── frontend/               # Next.js 16 + Tailwind CSS + shadcn/ui
├── backend/                # FastAPI REST API
│   ├── main.py             # App factory, CORS, router registration
│   ├── config.py           # Pydantic Settings (env vars)
│   ├── database.py         # SQLAlchemy engine, session, init_db()
│   ├── routers/            # One file per resource
│   ├── services/
│   │   └── market_data.py  # yfinance quote + OHLCV fetching
│   └── models/             # Pydantic request/response + SQLAlchemy ORM models
├── data/                   # ML + data ingestion layer
│   ├── ingest/             # OHLCV fetch, indicator compute, DB store
│   ├── sentiment/          # Moneycontrol RSS → FinBERT → daily aggregate
│   ├── signals/            # Technical + sentiment + momentum composite
│   └── alerts/             # Signal changes, sentiment shifts, drift checks
├── math_engine/            # Mathematical models
│   ├── optimizer/          # PyPortfolioOpt: min_vol / max_sharpe / efficient_return
│   └── risk/               # Monte Carlo VaR/CVaR engine
├── notifications/          # Notification utilities
├── scripts/
│   ├── run_daily_pipeline.py  # Orchestrates all pipeline steps
│   ├── seed_nifty50.py        # One-time Nifty 50 DB seed
│   └── test_pipeline.py       # Smoke test
├── docs/                   # Architecture notes
└── requirements.txt        # All Python dependencies
```

## Commands

```bash
# Activate venv first (Windows)
.venv/Scripts/activate

# Initialize DB
python -c "from backend.database import init_db; init_db()"

# Seed stocks
python scripts/seed_nifty50.py

# Full daily pipeline
python scripts/run_daily_pipeline.py

# Backend API
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Smoke test
python scripts/test_pipeline.py
```

## Conventions

- Database: SQLAlchemy + SQLite (local file `niveshsutra.db` in project root)
- No auth: single local user, `DEFAULT_USER_ID` defined in `backend/database.py`
- Stock symbols in DB without `.NS` suffix; `.NS` appended for yfinance
- All monetary values in INR
- Market data imported from `backend.services.market_data`
- Pipeline uses SQLAlchemy sessions for all DB access

## Environment

- Copy `.env.example` to `.env` and adjust as needed
- Python venv: `python -m venv .venv`
- Install deps: `pip install -r requirements.txt`
- Frontend: `cd frontend && npm install`

## Database

- SQLAlchemy ORM with SQLite backend
- Schema defined in SQLAlchemy models (no external migrations needed)
- `init_db()` in `backend/database.py` creates all tables

## Pipeline

- Run manually: `python scripts/run_daily_pipeline.py`
- Steps: OHLCV ingest -> indicators -> sentiment -> signals -> alerts
- Best run daily after NSE market close (15:30 IST)

## Architecture

- Backend: FastAPI on port 8000
- Frontend: Next.js on port 3000
- Frontend talks to backend via `NEXT_PUBLIC_API_BASE_URL`
- No cloud dependencies -- everything runs locally
