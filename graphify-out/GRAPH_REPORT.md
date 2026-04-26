# Graph Report - .  (2026-04-26)

## Corpus Check
- 92 files · ~36,657 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 474 nodes · 802 edges · 96 communities detected
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 303 edges (avg confidence: 0.8)
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
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]

## God Nodes (most connected - your core abstractions)
1. `Table()` - 82 edges
2. `GET()` - 70 edges
3. `get_anon_client()` - 19 edges
4. `get_authed_client()` - 18 edges
5. `search_instrument()` - 15 edges
6. `request_json()` - 14 edges
7. `get_supabase()` - 13 edges
8. `run_sentiment_pipeline()` - 13 edges
9. `fetch_live_quotes_batch()` - 13 edges
10. `get_quote_with_fallback()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `list_alerts()` --calls--> `Table()`  [INFERRED]
  backend\routers\alerts.py → frontend\components\ui\table.tsx
- `mark_read()` --calls--> `Table()`  [INFERRED]
  backend\routers\alerts.py → frontend\components\ui\table.tsx
- `mark_all_read()` --calls--> `Table()`  [INFERRED]
  backend\routers\alerts.py → frontend\components\ui\table.tsx
- `list_holdings()` --calls--> `Table()`  [INFERRED]
  backend\routers\holdings.py → frontend\components\ui\table.tsx
- `list_holdings_live()` --calls--> `fetch_live_quotes_batch()`  [INFERRED]
  backend\routers\holdings.py → streamlit_app\live_market.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (38): list_alerts(), mark_all_read(), mark_read(), create_holding(), delete_holding(), list_holdings(), list_holdings_live(), update_holding() (+30 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (36): fetch_alerts(), fetch_latest_signals(), fetch_market_sentiment(), fetch_nifty50(), fetch_portfolio_performance(), fetch_watchlist_live(), add_stock(), fetch_stocks() (+28 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (36): compute_indicators(), Compute technical indicators for each stock symbol using pandas-ta. Indicators:, Compute technical indicators for each symbol in the OHLCV DataFrame.      Args:, Safely extract and round a value from a pandas Series., _safe_round(), get_supabase(), aggregate_daily(), fetch_news() (+28 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (39): main(), NiveshSutra — Streamlit Entry Point.  Flow:   1. Not logged in   → show Login /, render_auth(), render_onboarding(), get_access_token(), get_github_oauth_url(), get_user_id(), handle_oauth_tokens() (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (38): BaseSettings, get_settings(), Settings, _cache_key(), _cache_ttl_seconds(), _candidate_tickers(), _coerce_float(), _coerce_int() (+30 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (30): _render_sidebar(), _render_sidebar(), _render_sidebar(), _render_sidebar(), render_signal_row(), _render_sidebar(), _render_sidebar(), render_sidebar() (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (18): fetch_ohlcv(), get_stock_list(), Fetch OHLCV data for all active stocks using yfinance-backed market data helpers, Read all stocks from Supabase stocks table., Fetch OHLCV data for all active stocks using free market data providers.      Ar, _candidate_tickers(), _coerce_float(), _coerce_int() (+10 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (17): _format_signal(), Email notification service using Resend API.  Sends signal change alerts to user, Send an email notifying the user that a tracked signal has changed.      Returns, send_signal_change_email(), _signal_color(), _check_signal_change_notifications(), compute_momentum_score(), compute_technical_score() (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (13): _check_rebalance_drift(), _check_sentiment_shifts(), _check_signal_changes(), _equal_weight_fallback(), generate_alerts(), Notification services for NiveshSutra., Flag symbols whose daily sentiment shifted significantly., For each user with a completed optimization, check if current portfolio     has (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (12): BaseModel, HoldingCreate, HoldingUpdate, get_tracked_signals(), NotificationPreference, Get all actively tracked signal notifications for the current user., Stop tracking a signal notification., stop_tracking_signal() (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.25
Nodes (11): Exception, HoldingInput, MonteCarloRiskError, _nearest_psd(), _normalize_holdings(), _price_matrix_from_supabase(), run_monte_carlo_var(), _var_cvar() (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.24
Nodes (8): fetchLiveQuoteMap(), fetchRiskSummary(), formatINR(), pnlColor(), PortfolioPage(), StocksPage(), createSupabaseAdminClient(), createSupabaseServerClient()

### Community 12 - "Community 12"
Cohesion: 0.53
Nodes (5): get_api_base_url(), get_required_setting(), get_setting(), Runtime configuration helpers for local and hosted Streamlit environments., _streamlit_secret()

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (2): handleSubmit(), createClient()

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (2): Badge(), cn()

### Community 15 - "Community 15"
Cohesion: 0.67
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 0.67
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
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): Compare today's signals with yesterday's and flag changes.

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Flag symbols whose daily sentiment shifted significantly.

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): For each user with a completed optimization, check if current portfolio     has

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Safely extract and round a value from a pandas Series.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Upsert OHLCV rows to Supabase ohlcv table.      Args:         df: DataFrame with

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): Upsert indicator rows to Supabase technical_indicators table.      Args:

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Upsert news articles to Supabase news_articles table.

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Upsert article sentiments to Supabase article_sentiments table.

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Upsert daily aggregated sentiment to Supabase sentiment_daily table.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Upsert signals to Supabase signals table.

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): Convert DataFrame to list of dicts, replacing NaN with None.

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Run portfolio optimization for a user.      Args:         user_id: UUID of the u

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Equal-weight fallback when optimization fails (singular matrix, etc.).

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Normalize RSI into [-1, +1].     30 (oversold) -> +1, 50 -> 0, 70 (overbought) -

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Normalize MACD histogram into [-1, +1].     Positive histogram -> bullish (+), n

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Normalize Bollinger Band position into [-1, +1].     Close near lower band -> +1

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Normalize OBV trend into [-1, +1].     Computes slope of last 20 OBV values via

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): technical_score = 0.3*RSI + 0.3*MACD + 0.2*BB + 0.2*OBV

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): momentum_score = mean(5d_return, 20d_return, SMA_crossover)     Each normalized

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): composite = 0.4*tech + 0.3*sent + 0.3*momentum      Returns (composite_score, si

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Generate a template-based human-readable explanation.

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Read indicators + sentiment from Supabase, compute signals for all stocks,     a

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Check all active signal notifications. If a tracked signal has changed,     send

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): Render the shared authenticated sidebar.

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Render the unauthenticated landing and auth flows.

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Render the risk questionnaire.

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): Call at the top of every protected page.     Redirects to app.py if session is m

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): Re-fetch profile from DB and update session state.

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): Inject the shared CSS skin once per page.

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (1): Render the shared sidebar shell.

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): Render a large editorial hero block.

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): Render a row of branded metric cards.

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (1): Render a short information band.

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Render a compact explanatory card.

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): Apply the shared visual theme to Plotly figures.

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): Fetch stocks from the live FastAPI market endpoint.

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Validate and add a symbol through the FastAPI backend.

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): Fetch stocks with latest close price and signal.

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (1): Validate and add a symbol through the FastAPI backend.

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): Return a Supabase client that sends the user JWT on every PostgREST call.

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): Format a number as INR currency string.

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): Given a list of answer scores, return (total_score, risk_profile).

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): Dashboard — portfolio overview, Nifty 50, sentiment, signals, watchlist, alerts.

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): Stocks — browse/filter Nifty 50 + all stocks, add custom stocks.

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (1): Fetch stocks with latest close price and signal.

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (1): Validate a symbol and upsert it into the stocks table.

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (1): Stock Detail — candlestick chart, technical indicators, sentiment, news.

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (1): Signals — AI trading signals with risk-profile personalization.

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (1): Portfolio — holdings table, P&L metrics, allocation pie, MVO optimization.

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (1): Settings — profile update, risk re-assessment, notification preferences.

## Knowledge Gaps
- **109 isolated node(s):** `Get all actively tracked signal notifications for the current user.`, `Stop tracking a signal notification.`, `Search for a stock by symbol. If it exists in the DB, return it.     If not, val`, `Fetch last 90 days of OHLCV data for a newly added stock.`, `CLI entry point: orchestrates OHLCV fetch -> compute indicators -> store in Supa` (+104 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 17`** (2 nodes): `main.py`, `root()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (2 nodes): `health.py`, `health_check()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `layout.tsx`, `RootLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `page.tsx`, `Home()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `loading.tsx`, `StocksLoading()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `LiveNiftyQuote.tsx`, `LiveNiftyQuote()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `LiveNiftyStat.tsx`, `LiveNiftyStat()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `NiftySparkline.tsx`, `NiftySparkline()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `SignalBadge.tsx`, `SignalBadge()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `SignalsTable.tsx`, `fmt()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `separator.tsx`, `cn()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `skeleton.tsx`, `Skeleton()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `app.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `loading.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `loading.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `Navbar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `StatCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `Compare today's signals with yesterday's and flag changes.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Flag symbols whose daily sentiment shifted significantly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `For each user with a completed optimization, check if current portfolio     has`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Safely extract and round a value from a pandas Series.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Upsert OHLCV rows to Supabase ohlcv table.      Args:         df: DataFrame with`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `Upsert indicator rows to Supabase technical_indicators table.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Upsert news articles to Supabase news_articles table.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Upsert article sentiments to Supabase article_sentiments table.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Upsert daily aggregated sentiment to Supabase sentiment_daily table.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Upsert signals to Supabase signals table.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Convert DataFrame to list of dicts, replacing NaN with None.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Run portfolio optimization for a user.      Args:         user_id: UUID of the u`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Equal-weight fallback when optimization fails (singular matrix, etc.).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Normalize RSI into [-1, +1].     30 (oversold) -> +1, 50 -> 0, 70 (overbought) -`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Normalize MACD histogram into [-1, +1].     Positive histogram -> bullish (+), n`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Normalize Bollinger Band position into [-1, +1].     Close near lower band -> +1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Normalize OBV trend into [-1, +1].     Computes slope of last 20 OBV values via`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `technical_score = 0.3*RSI + 0.3*MACD + 0.2*BB + 0.2*OBV`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `momentum_score = mean(5d_return, 20d_return, SMA_crossover)     Each normalized`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `composite = 0.4*tech + 0.3*sent + 0.3*momentum      Returns (composite_score, si`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Generate a template-based human-readable explanation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Read indicators + sentiment from Supabase, compute signals for all stocks,     a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Check all active signal notifications. If a tracked signal has changed,     send`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `Render the shared authenticated sidebar.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Render the unauthenticated landing and auth flows.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Render the risk questionnaire.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Call at the top of every protected page.     Redirects to app.py if session is m`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `Re-fetch profile from DB and update session state.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `Inject the shared CSS skin once per page.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `Render the shared sidebar shell.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `Render a large editorial hero block.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `Render a row of branded metric cards.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `Render a short information band.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Render a compact explanatory card.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `Apply the shared visual theme to Plotly figures.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `Fetch stocks from the live FastAPI market endpoint.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Validate and add a symbol through the FastAPI backend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `Fetch stocks with latest close price and signal.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `Validate and add a symbol through the FastAPI backend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `Return a Supabase client that sends the user JWT on every PostgREST call.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `Format a number as INR currency string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `Given a list of answer scores, return (total_score, risk_profile).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `Dashboard — portfolio overview, Nifty 50, sentiment, signals, watchlist, alerts.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `Stocks — browse/filter Nifty 50 + all stocks, add custom stocks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `Fetch stocks with latest close price and signal.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `Validate a symbol and upsert it into the stocks table.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `Stock Detail — candlestick chart, technical indicators, sentiment, news.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `Signals — AI trading signals with risk-profile personalization.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `Portfolio — holdings table, P&L metrics, allocation pie, MVO optimization.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `Settings — profile update, risk re-assessment, notification preferences.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GET()` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 12`?**
  _High betweenness centrality (0.245) - this node is a cross-community bridge._
- **Why does `Table()` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.229) - this node is a cross-community bridge._
- **Why does `run_sentiment_pipeline()` connect `Community 2` to `Community 0`, `Community 8`, `Community 5`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `Table()` (e.g. with `list_alerts()` and `mark_read()`) actually correct?**
  _`Table()` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 66 inferred relationships involving `GET()` (e.g. with `list_holdings_live()` and `market_overview()`) actually correct?**
  _`GET()` has 66 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `get_anon_client()` (e.g. with `login()` and `signup()`) actually correct?**
  _`get_anon_client()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `get_authed_client()` (e.g. with `render_onboarding()` and `_load_profile()`) actually correct?**
  _`get_authed_client()` has 16 INFERRED edges - model-reasoned connections that need verification._