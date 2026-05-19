# NiveshSutra

AI-powered Indian equity intelligence platform. Technical analysis, NLP sentiment scoring, and portfolio optimization for Nifty 50 stocks.

## Features

- **Market Data Pipeline** -- Daily OHLCV ingestion with 14+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **Sentiment Analysis** -- FinBERT NLP on financial news from MoneyControl, Economic Times, and RSS feeds
- **Composite Signals** -- Weighted technical + sentiment + momentum scoring with buy/sell/hold signals
- **Portfolio Optimization** -- Mean-variance optimization (PyPortfolioOpt) with Monte Carlo risk analysis
- **Real-time Dashboard** -- Next.js frontend with live prices, interactive charts, and signal tables

## Architecture

```
Backend:   FastAPI + SQLAlchemy (SQLite)
Frontend:  Next.js 16 + Tailwind CSS + shadcn/ui + Recharts
Pipeline:  yfinance + jugaad-data + HuggingFace FinBERT
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Clone and install

```bash
git clone <repo-url> && cd NiveshSutra
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize database

```bash
python -c "from backend.database import init_db; init_db()"
python scripts/seed_nifty50.py
```

### 3. Run the data pipeline

```bash
python scripts/run_daily_pipeline.py
```

This fetches OHLCV data, computes technical indicators, runs sentiment analysis, and generates composite signals. Run daily for fresh data.

### 4. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 5. Start the frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

Open http://localhost:3000

## Project Structure

```
NiveshSutra/
  backend/           FastAPI application
    routers/         API endpoints
    models/          Pydantic + SQLAlchemy models
    services/        Market data service
    database.py      SQLAlchemy engine and session
  data/              Data pipeline
    ingest/          OHLCV fetch + indicator computation
    sentiment/       FinBERT news sentiment
    signals/         Composite signal generation
    alerts/          Alert generation
  math_engine/       Quantitative models
    optimizer/       Mean-variance portfolio optimization
    risk/            Monte Carlo VaR/CVaR
  frontend/          Next.js dashboard
  scripts/           CLI utilities
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/v1/stocks` | List all stocks |
| `GET /api/v1/stocks/live` | Stocks with live prices |
| `GET /api/v1/signals` | Latest composite signals |
| `GET /api/v1/stocks/{symbol}/ohlcv` | OHLCV history |
| `GET /api/v1/stocks/{symbol}/sentiment` | Sentiment history |
| `GET /api/v1/market/overview` | Market overview |
| `GET /api/v1/holdings` | Portfolio holdings |
| `POST /api/v1/portfolio/risk` | Monte Carlo risk analysis |
| `GET /docs` | Interactive API documentation |

## License

MIT
