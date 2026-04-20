# Graph Report - .  (2026-04-20)

## Corpus Check
- 55 files · ~25,057 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 343 nodes · 497 edges · 36 communities detected
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 119 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]

## God Nodes (most connected - your core abstractions)
1. `get_authed_client()` - 18 edges
2. `get_anon_client()` - 17 edges
3. `search_instrument()` - 14 edges
4. `get_supabase()` - 13 edges
5. `run_sentiment_pipeline()` - 11 edges
6. `get_quote_with_fallback()` - 10 edges
7. `run_signals_pipeline()` - 10 edges
8. `render_auth()` - 10 edges
9. `render_onboarding()` - 10 edges
10. `get_profile()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `run_signals_pipeline()`  [INFERRED]
  NiveshSutra\scripts\run_daily_pipeline.py → NiveshSutra\services\ml\signals\__init__.py
- `main()` --calls--> `generate_alerts()`  [INFERRED]
  NiveshSutra\scripts\run_daily_pipeline.py → NiveshSutra\services\ml\alerts\__init__.py
- `main()` --calls--> `get_supabase()`  [INFERRED]
  NiveshSutra\scripts\seed_nifty50.py → NiveshSutra\services\ml\config.py
- `market_index_overview()` --calls--> `get_quote_with_fallback()`  [INFERRED]
  NiveshSutra\services\api\routers\market.py → NiveshSutra\services\api\services\market_data.py
- `portfolio_performance()` --calls--> `run_optimization()`  [INFERRED]
  NiveshSutra\services\api\routers\portfolio.py → NiveshSutra\services\ml\optimizer\__init__.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (43): BaseSettings, get_settings(), Settings, Exception, list_holdings_live(), _cache_key(), _cache_ttl_seconds(), _candidate_tickers() (+35 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (47): _render_sidebar(), _render_sidebar(), _render_sidebar(), _render_sidebar(), _render_sidebar(), _render_sidebar(), main(), NiveshSutra — Streamlit Entry Point.  Flow:   1. Not logged in   → show Login / (+39 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (39): get_supabase(), aggregate_daily(), fetch_news(), _get_finbert(), _iter_moneycontrol_results(), map_articles_to_symbols(), _normalize_news_item(), _parse_moneycontrol_datetime() (+31 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (26): fetch_alerts(), fetch_latest_signals(), fetch_market_sentiment(), fetch_nifty50(), fetch_portfolio_performance(), fetch_watchlist_live(), fetch_indicators(), fetch_latest_signal() (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (22): _check_signal_change_notifications(), compute_composite(), compute_momentum_score(), compute_technical_score(), generate_explanation(), normalize_bb(), normalize_macd(), normalize_obv() (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (15): _check_rebalance_drift(), _check_sentiment_shifts(), _check_signal_changes(), _equal_weight_fallback(), generate_alerts(), Notification services for NiveshSutra., Flag symbols whose daily sentiment shifted significantly., For each user with a completed optimization, check if current portfolio     has (+7 more)

### Community 6 - "Community 6"
Cohesion: 0.1
Nodes (10): BaseModel, HoldingCreate, HoldingUpdate, get_tracked_signals(), NotificationPreference, Get all actively tracked signal notifications for the current user., Stop tracking a signal notification., stop_tracking_signal() (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (10): accept_signal(), render_signal_row(), compute_risk_profile(), format_currency(), format_signal(), get_position_size_hint(), Shared utilities: formatting, signal colors, personalization logic., Given a list of answer scores, return (total_score, risk_profile). (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (12): add_stock(), fetch_stocks(), Validate and add a symbol through the FastAPI backend., Fetch stocks with latest close price and signal., _build_url(), Thin HTTP client for calling the separately hosted FastAPI service., request_json(), get_api_base_url() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.4
Nodes (5): fetch_ohlcv(), get_stock_list(), Fetch OHLCV data for all active stocks using yfinance-backed market data helpers, Read all stocks from Supabase stocks table., Fetch OHLCV data for all active stocks using free market data providers.      Ar

### Community 10 - "Community 10"
Cohesion: 0.4
Nodes (5): compute_indicators(), Compute technical indicators for each stock symbol using pandas-ta. Indicators:, Compute technical indicators for each symbol in the OHLCV DataFrame.      Args:, Safely extract and round a value from a pandas Series., _safe_round()

### Community 11 - "Community 11"
Cohesion: 0.47
Nodes (5): _format_signal(), Email notification service using Resend API.  Sends signal change alerts to user, Send an email notifying the user that a tracked signal has changed.      Returns, send_signal_change_email(), _signal_color()

### Community 12 - "Community 12"
Cohesion: 0.4
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Return a Supabase client that sends the user JWT on every PostgREST call.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Format a number as INR currency string.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Given a list of answer scores, return (total_score, risk_profile).

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Dashboard — portfolio overview, Nifty 50, sentiment, signals, watchlist, alerts.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Stocks — browse/filter Nifty 50 + all stocks, add custom stocks.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Fetch stocks with latest close price and signal.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Validate a symbol and upsert it into the stocks table.

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Stock Detail — candlestick chart, technical indicators, sentiment, news.

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Signals — AI trading signals with risk-profile personalization.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Portfolio — holdings table, P&L metrics, allocation pie, MVO optimization.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Settings — profile update, risk re-assessment, notification preferences.

## Knowledge Gaps
- **86 isolated node(s):** `Daily pipeline orchestrator.  Runs the full NiveshSutra ML pipeline in order:`, `Seed script: insert all 50 Nifty 50 stocks into the stocks table.  Usage:     py`, `Get all actively tracked signal notifications for the current user.`, `Stop tracking a signal notification.`, `Search for a stock by symbol. If it exists in the DB, return it.     If not, val` (+81 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 16`** (2 nodes): `root()`, `main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `health_check()`, `health.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Return a Supabase client that sends the user JWT on every PostgREST call.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Format a number as INR currency string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Given a list of answer scores, return (total_score, risk_profile).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Dashboard — portfolio overview, Nifty 50, sentiment, signals, watchlist, alerts.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Stocks — browse/filter Nifty 50 + all stocks, add custom stocks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Fetch stocks with latest close price and signal.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Validate a symbol and upsert it into the stocks table.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Stock Detail — candlestick chart, technical indicators, sentiment, news.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Signals — AI trading signals with risk-profile personalization.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Portfolio — holdings table, P&L metrics, allocation pie, MVO optimization.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Settings — profile update, risk re-assessment, notification preferences.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_supabase()` connect `Community 2` to `Community 9`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.329) - this node is a cross-community bridge._
- **Why does `get_authed_client()` connect `Community 3` to `Community 8`, `Community 1`, `Community 7`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 2` to `Community 10`, `Community 3`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `get_authed_client()` (e.g. with `render_onboarding()` and `_load_profile()`) actually correct?**
  _`get_authed_client()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `get_anon_client()` (e.g. with `login()` and `signup()`) actually correct?**
  _`get_anon_client()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `search_instrument()` (e.g. with `search_stock()` and `add_stock()`) actually correct?**
  _`search_instrument()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `get_supabase()` (e.g. with `main()` and `generate_alerts()`) actually correct?**
  _`get_supabase()` has 12 INFERRED edges - model-reasoned connections that need verification._