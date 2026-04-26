# NiveshSutra

NiveshSutra is an Indian equity intelligence and portfolio risk platform for NSE-listed stocks. It combines live market data, technical indicators, news sentiment, portfolio optimization, and Monte Carlo risk analytics into a Supabase-backed product workflow.

The project is designed as a full-stack fintech system, not just a dashboard: it has authenticated user workflows, live quote fallbacks, portfolio storage, backend APIs, a daily data pipeline, optimizer logic, and a quantitative risk engine that explains downside exposure in rupee terms.

## Recruiter Snapshot

This project demonstrates practical finance engineering across product, data, backend, and quantitative layers:

| Area | What it shows |
| --- | --- |
| Quantitative finance | Monte Carlo VaR/CVaR engine, covariance modeling, portfolio simulation, risk-adjusted optimization |
| Backend engineering | FastAPI service layer, authenticated Supabase access, deployment-ready routing, compatibility shims |
| Data engineering | Free market-data provider fallbacks, OHLCV ingestion, daily signal/sentiment pipeline |
| Frontend/product | Streamlit investor workflow, Next.js quote surface, clean dark trading UI |
| Reliability | Graceful fallbacks for stale prices, optimizer failures, unavailable risk-free-rate data, and missing optional libraries |

## Why This Project Is Valuable

Most portfolio apps stop at showing holdings and returns. NiveshSutra adds the parts an investor actually needs before making a decision:

- **Live market context:** NSE quotes are refreshed through free provider fallbacks instead of relying on stale stored values.
- **Portfolio intelligence:** Holdings are marked to market and connected to watchlists, alerts, technical signals, and sentiment.
- **Optimization:** The system can recommend allocations for conservative, moderate, and aggressive profiles.
- **Risk visibility:** The Monte Carlo engine estimates how much the portfolio could lose under thousands of plausible market scenarios.
- **Production shape:** The app has a real backend, database/auth layer, deployment configuration, and repeatable verification commands.

## Core Features

- Live Indian equity quote pipeline using free sources: `jugaad-data`, Moneycontrol snapshots, yfinance fallback, and Supabase OHLCV fallback.
- Supabase-backed portfolio ledger with holdings, watchlists, signals, alerts, and optimization history.
- Mean-variance portfolio optimizer with a NumPy/Pandas fallback when PyPortfolioOpt is unavailable.
- Monte Carlo risk engine that simulates 10,000+ scenarios and reports VaR/CVaR at 95% and 99% confidence.
- Daily pipeline for OHLCV refresh, technical indicators, news sentiment, signals, and alert generation.
- Streamlit dark trading UI using a restrained financial palette:
  - Background: `#0B0E14`
  - Surface/cards: `#161B22`
  - Primary action: `#2F80ED`
  - Secondary text: `#8B949E`
  - Gain: `#23C55E`
  - Loss: `#EF4444`
- Render-ready FastAPI deployment with a cron pipeline blueprint.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Streamlit UI | Streamlit, Plotly |
| Web UI | Next.js, React, TypeScript, Tailwind, Recharts |
| API | FastAPI, Uvicorn |
| Database/Auth | Supabase Postgres, Supabase Auth, Row Level Security |
| Market data | jugaad-data, Moneycontrol, yfinance |
| Analytics | NumPy, Pandas |
| Risk engine | Vectorized Monte Carlo simulation |
| Optimization | NumPy/Pandas fallback, optional PyPortfolioOpt |
| Deployment | Render, Streamlit Community Cloud, optional Vercel |

## Architecture

```text
Streamlit app
  -> Supabase Auth
  -> Supabase user data
  -> FastAPI endpoints for live holdings, optimizer, and risk

Next.js app
  -> Supabase browser auth
  -> Next API quote proxy
  -> FastAPI market and portfolio endpoints

FastAPI backend
  -> Supabase service-role or user-JWT clients
  -> market data service with free provider fallbacks
  -> portfolio optimizer
  -> Monte Carlo VaR/CVaR engine
  -> alerts, signals, sentiment, holdings, watchlist routes

Daily pipeline
  -> fetch OHLCV
  -> compute indicators
  -> fetch and score news
  -> generate signals
  -> generate alerts
```

## Repository Layout

```text
NiveshSutra/
|-- backend/                    FastAPI app, routers, models, market data services
|-- streamlit_app/              Primary Streamlit product UI
|-- frontend/                   Next.js web UI
|-- math_engine/
|   |-- optimizer/              Portfolio optimizer
|   `-- risk/                   Monte Carlo VaR/CVaR engine
|-- data/                       Pipeline helpers for sentiment, signals, alerts
|-- notifications/              Notification utilities
|-- scripts/                    Seed and daily pipeline entrypoints
|-- services/api/               Compatibility shim for older Render paths
|-- supabase/migrations/        Database schema and RLS policies
|-- docs/                       Architecture notes
|-- render.yaml                 Render web service and cron blueprint
|-- requirements.txt            Streamlit/shared Python dependencies
|-- backend/requirements.txt    FastAPI backend dependencies
`-- .env.example                Environment variable template
```

## Market Data

NiveshSutra uses free market-data sources only.

Provider order for live quotes:

1. `jugaad-data` NSE live quote APIs for Indian equities.
2. Moneycontrol snapshots for index fallback.
3. yfinance fallback for historical and quote data.
4. Supabase OHLCV rows when external providers are unavailable.

This makes the UI more resilient: if one source fails or returns stale data, the backend attempts another source before falling back to stored data.

Historical returns for optimization and risk are read from Supabase `ohlcv` rows. The system expects clean close prices per symbol and uses overlapping daily observations across assets so the covariance matrix is based on aligned market history.

## Portfolio Optimizer

The optimizer supports three user profiles:

| Risk profile | Method |
| --- | --- |
| Conservative | Minimum volatility |
| Moderate | Maximum Sharpe ratio |
| Aggressive | Higher target return / efficient return style |

If PyPortfolioOpt is not installed or fails, NiveshSutra runs a free vectorized NumPy/Pandas optimizer that samples long-only portfolios, computes annualized return/risk, and selects the best allocation for the user's risk profile.

The optimizer writes to:

- `portfolio_optimizations`
- `optimization_allocations`

## Monte Carlo Risk Engine

The Monte Carlo engine answers a practical investor question: **"How much could this portfolio lose if the market moves against me?"**

It lives in `math_engine/risk/` and is exposed through:

```text
POST /api/v1/portfolio/risk
```

### What It Does

- Simulates at least **10,000 correlated market scenarios** for a multi-asset portfolio.
- Uses daily log returns from Supabase OHLCV history.
- Builds an asset covariance and correlation matrix from overlapping historical observations.
- Repairs non-positive-semidefinite covariance matrices with eigenvalue clipping so simulation remains numerically stable.
- Generates portfolio-level profit/loss distributions with vectorized NumPy operations.
- Reports **Value-at-Risk (VaR)** and **Conditional Value-at-Risk (CVaR)** at **95%** and **99%** confidence levels.
- Uses a default **756-trading-day lookback** of market history.
- Uses RBI risk-free-rate data through `jugaad-data` when available, with a conservative fallback rate.

### Why It Adds Value

VaR estimates the loss threshold at a confidence level. For example, a 95% one-day VaR of `Rs 20,000` means the model estimates that losses should not exceed `Rs 20,000` on 95% of simulated days.

CVaR goes further by measuring the average loss inside the worst tail. If CVaR 95 is `Rs 31,000`, the portfolio's worst 5% simulated outcomes average a `Rs 31,000` loss. This is more useful than VaR alone because it describes tail severity, not only the cutoff point.

For a recruiter or reviewer, this section is important because it shows the project is not only displaying financial data. It is transforming raw holdings and historical prices into a risk decision system:

- Investors can compare upside expectations against downside exposure.
- Portfolio concentration becomes visible through correlation-aware simulation.
- Risk is expressed in rupees and percentages, which is understandable to a real user.
- The backend can serve risk metrics quickly enough for a web workflow because the core math is vectorized.

Example request body:

```json
{
  "scenarios": 10000,
  "horizon_days": 1,
  "lookback_days": 756,
  "confidence_levels": [0.95, 0.99],
  "seed": 42
}
```

## API Routes

FastAPI routes are mounted under `/api/v1`.

| Area | Routes |
| --- | --- |
| Health | `GET /health` |
| Stocks | `GET /stocks/live`, `GET /stocks/{symbol}/quote` |
| Market | `GET /market/index-overview` |
| Holdings | `GET /holdings/live` plus CRUD routes |
| Watchlist | Watchlist CRUD and live quote enrichment |
| Portfolio | `POST /portfolio/optimize`, `POST /portfolio/risk`, performance and optimization history |
| Signals | Signal list, tracking, and accepted signal workflows |
| Alerts | Alert generation and read/update routes |
| Notifications | Notification utilities |

## Environment Variables

Copy `.env.example` to `.env` for local Python services.

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

For the Next.js app, also set the matching public Supabase variables in `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000
```

`SUPABASE_SERVICE_ROLE_KEY` is strongly recommended for the backend. When it is absent, selected authenticated routes use the caller's JWT so RLS still works, but service role is the cleaner production setup.

## Local Setup

### 1. Install Python Dependencies

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r backend/requirements.txt
```

`services/api/requirements.txt` is a compatibility shim for older Render settings and points to `backend/requirements.txt`.

### 2. Apply Supabase Migrations

Apply the SQL files in `supabase/migrations/` in order:

```text
001_foundation.sql
002_market_data.sql
003_sentiment.sql
004_signals.sql
005_portfolio_optimization.sql
006_alerts.sql
007_signal_tracking_and_notifications.sql
008_allow_authenticated_stock_inserts.sql
```

### 3. Seed the Nifty 50 Universe

```bash
python scripts/seed_nifty50.py
```

### 4. Run the FastAPI Backend

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Useful checks:

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/docs
```

### 5. Run the Streamlit App

```bash
python -m streamlit run streamlit_app/app.py
```

Open `http://localhost:8501`.

### 6. Run the Next.js App

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Daily Pipeline

Run the full daily pipeline:

```bash
python scripts/run_daily_pipeline.py --days 365
```

This updates OHLCV, indicators, sentiment, signals, and alerts depending on configured Supabase data and available providers.

## Deployment

### Render FastAPI Service

`render.yaml` defines:

- Web service: `niveshsutra-api`
- Build command: `python -m pip install -r backend/requirements.txt`
- Start command: `python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}`
- Health check: `/api/v1/health`
- Cron job: `niveshsutra-daily-pipeline`

If an older Render dashboard setting still points at `services.api.main:app`, the compatibility module in `services/api/main.py` re-exports the real `backend.main:app`.

### Streamlit Community Cloud

Use:

- App file: `streamlit_app/app.py`
- Dependencies: root `requirements.txt`
- Secrets: values from `.env.example`

### Vercel or Local Next.js

The `frontend/` app can run independently and proxy quotes through the FastAPI backend. Set `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.

## Verification Commands

```bash
python -m compileall backend math_engine streamlit_app

cd frontend
npm run lint
npm run build
```

For a quick API quote smoke test:

```bash
curl "http://127.0.0.1:8000/api/v1/market/index-overview"
```

## What Reviewers Should Notice

- The project has a real product workflow: auth, onboarding, holdings, watchlists, optimization, risk, alerts, and market data.
- The risk engine is integrated into the API layer instead of living as an isolated notebook.
- The implementation prioritizes free data sources and robust fallbacks, which is important for deployable personal-finance tooling.
- The codebase separates UI, backend, analytics, data pipeline, and database migrations clearly enough for future extension.
- The Monte Carlo implementation uses vectorized NumPy/Pandas operations, making the system suitable for interactive web latency rather than offline-only analysis.

## Graphify

This repository includes a graphify knowledge graph in `graphify-out/`.

After changing code files, update it with:

```bash
python -m graphify update .
```

## Disclaimer

NiveshSutra is for educational and portfolio purposes. It is not financial advice, investment advice, or a trading recommendation engine.

## License

MIT
