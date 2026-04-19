# NiveshSutra

AI-powered Indian equity wealth management platform combining technical analysis, NLP sentiment scoring, and Modern Portfolio Theory into a hybrid signal engine for Nifty 50 stocks.

## What It Does

NiveshSutra ingests daily market data for all 50 Nifty 50 stocks, computes technical indicators (RSI, MACD, Bollinger Bands, OBV), runs FinBERT sentiment analysis on financial news, and produces explainable buy/hold/sell signals through a weighted composite score. It also optimizes portfolio allocations using Mean-Variance Optimization (PyPortfolioOpt) tailored to each user's risk profile.

### Signal Engine

```
composite = 0.4 * technical + 0.3 * sentiment + 0.3 * momentum

technical = 0.3*RSI + 0.3*MACD + 0.2*BB + 0.2*OBV  (normalized -1 to +1)
momentum  = mean(5d_return, 20d_return, SMA_crossover)
sentiment = avg(positive_prob - negative_prob) from FinBERT

Score -> Signal:  >= 0.5 strong_buy | >= 0.2 buy | >= -0.2 hold | >= -0.5 sell | < -0.5 strong_sell
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Charts | Lightweight Charts (TradingView), Recharts |
| Backend | FastAPI, Python 3.14 |
| Database | Supabase (Postgres 17, Auth, RLS) |
| Market Data | yfinance quotes/history + Moneycontrol scraping |
| Indicators | pandas-ta (RSI, MACD, BB, SMA, EMA, ATR, OBV) |
| Sentiment | ProsusAI/finbert (HuggingFace Transformers) |
| News | Moneycontrol via `moneycontrol-api` |
| Optimization | PyPortfolioOpt (CAPM, Ledoit-Wolf, MVO) |

## Project Structure

```
NiveshSutra/
├── apps/web/              # Next.js 15 frontend
│   └── src/
│       ├── app/           # Pages (login, signup, dashboard, stocks, etc.)
│       ├── components/    # Sidebar, UI components
│       └── lib/           # Supabase client, API helper, auth context
├── services/
│   ├── api/               # FastAPI backend
│   │   ├── routers/       # Route handlers
│   │   ├── models/        # Pydantic models
│   │   └── dependencies.py # Auth middleware
│   └── ml/                # ML pipelines
│       ├── ingest/        # OHLCV fetch + indicator computation
│       ├── sentiment/     # Moneycontrol news + FinBERT pipeline
│       ├── signals/       # Hybrid signal engine
│       ├── optimizer/     # PyPortfolioOpt wrapper
│       └── alerts/        # Alert generator
├── supabase/migrations/   # 6 SQL migrations with RLS
├── scripts/               # Seed data, daily pipeline orchestrator
├── docs/                  # Architecture, research notes
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Supabase project (free tier works)

### 1. Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/NiveshSutra.git
cd NiveshSutra

# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd apps/web && npx pnpm install && cd ../..
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Also create `apps/web/.env.local` with the `NEXT_PUBLIC_*` variables.

### 3. Database Setup

Apply the 6 migrations to your Supabase project via the SQL editor (in order: 001 through 006), or use the Supabase CLI.

### 4. Seed Stock Data

```bash
python scripts/seed_nifty50.py
```

### 5. Run Data Pipeline

```bash
# Full pipeline: ingest -> sentiment -> signals -> alerts
python scripts/run_daily_pipeline.py

# Or run individual steps:
python -m services.ml.run_ingest --days 365
python -m services.ml.run_sentiment
python -m services.ml.run_signals
```

Note: The first run of the sentiment pipeline will download the FinBERT model (~440MB).

### 6. Start the App

```bash
# Terminal 1: Backend API
cd services/api && python -m uvicorn services.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/web && npx pnpm dev
```

Open http://localhost:3000 in your browser.

## Features

- **Risk-Profiled Onboarding**: 5-question questionnaire maps users to conservative/moderate/aggressive profiles
- **Stock Explorer**: Nifty 50 stocks with candlestick charts, technical indicators, and sentiment gauges
- **Hybrid Signals**: Explainable buy/sell recommendations combining technical, sentiment, and momentum scores
- **Portfolio Optimizer**: Mean-Variance Optimization with CAPM returns and Ledoit-Wolf covariance, tailored to risk profile
- **Sentiment Analysis**: FinBERT NLP scoring of financial news headlines from Indian sources
- **Alerts**: Automated notifications for signal changes, sentiment shifts, and portfolio drift
- **Dark Mode**: Dark-first responsive UI with shadcn/ui components

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/stocks | List all stocks |
| GET | /api/v1/stocks/{symbol} | Stock detail |
| GET | /api/v1/stocks/{symbol}/ohlcv | OHLCV history |
| GET | /api/v1/stocks/{symbol}/indicators | Technical indicators |
| GET | /api/v1/stocks/{symbol}/sentiment | Sentiment time series |
| GET | /api/v1/stocks/{symbol}/news | News articles |
| GET | /api/v1/signals | Latest signals |
| GET | /api/v1/signals/{symbol}/latest | Signal with decomposition |
| GET | /api/v1/sentiment/market | Market-wide sentiment |
| GET | /api/v1/market/overview | Gainers/losers |
| POST | /api/v1/portfolio/optimize | Run optimization |
| GET | /api/v1/portfolio/performance | Portfolio P&L |

All user-specific endpoints require a Bearer token from Supabase Auth.

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed system diagrams and data flow.

## Disclaimer

This is a portfolio/educational project. It is not financial advice. Do not make investment decisions based solely on this platform's signals. Always consult a qualified financial advisor.

## License

MIT
