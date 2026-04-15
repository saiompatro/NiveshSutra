# NiveshSutra

AI-powered Indian equity wealth management platform combining technical analysis, NLP sentiment, and portfolio optimization.

## Project Structure
- `apps/web/` — Next.js 15 frontend (pnpm)
- `services/api/` — FastAPI backend
- `services/ml/` — ML pipelines (ingest, sentiment, signals, optimizer)
- `supabase/migrations/` — Database migrations (already applied)
- `scripts/` — Seed data, daily pipeline orchestrator
- `docs/` — Architecture, research notes

## Commands
```bash
# Frontend
cd apps/web && npx pnpm dev

# Backend API
cd services/api && python -m uvicorn services.api.main:app --reload --port 8000

# From project root with venv activated:
.venv/Scripts/activate  # Windows

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
- API routes: `/api/v1/` prefix
- Auth: Supabase Auth, Bearer token in Authorization header
- Stock symbols in DB without `.NS` suffix; `.NS` appended for yfinance
- All monetary values in INR
- Dark mode first, Tailwind `dark:` classes
- shadcn/ui components in `src/components/ui/`

## Environment
- Copy `.env.example` to `.env` and fill in Supabase credentials
- Python venv: `python -m venv .venv`
- Frontend: `pnpm install` in `apps/web/`

## Database
- Supabase Postgres 17 (ap-south-1)
- 6 migrations applied (001-006)
- RLS enabled on all tables
- Auto-profile creation on signup via trigger
