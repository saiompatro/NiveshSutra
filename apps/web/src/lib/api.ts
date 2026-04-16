import { createClient } from "@/lib/supabase";

// ── Legacy helper (deprecated — use named functions below) ──────────
const configuredApiBase = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();
const API_BASE =
  configuredApiBase && !/^https?:\/\/localhost(?::\d+)?$/i.test(configuredApiBase)
    ? configuredApiBase.replace(/\/+$/, "")
    : "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** @deprecated Use the named Supabase functions instead. */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }

  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(message, res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Supabase-based data access layer ────────────────────────────────

function sb() {
  return createClient();
}

// ---------- Stocks ----------

export interface StockRow {
  symbol: string;
  company_name: string;
  sector: string;
  industry: string;
  market_cap_category: string;
  is_nifty50: boolean;
  active: boolean;
}

export interface StockWithPrice {
  symbol: string;
  company_name: string;
  sector: string;
  current_price: number;
  change_pct: number;
  signal?: string;
}

export interface StockDetail {
  symbol: string;
  company_name: string;
  sector: string;
  current_price: number;
  change_pct: number;
  change: number;
  day_high: number;
  day_low: number;
  volume: number;
  market_cap: number;
}

export interface StockSearchResult {
  stock: StockRow;
  source: string;
}

export async function searchAndAddStock(
  symbol: string
): Promise<StockSearchResult | null> {
  try {
    const result = await apiFetch<StockSearchResult>(
      `/stocks/search?q=${encodeURIComponent(symbol)}`
    );
    return result ?? null;
  } catch {
    // If server not available, check DB directly
    const supabase = sb();
    const { data } = await supabase
      .from("stocks")
      .select("*")
      .eq("symbol", symbol.toUpperCase())
      .single();
    return data ? { stock: data, source: "database" } : null;
  }
}

export async function fetchAllStockSymbols(): Promise<
  Array<{ symbol: string; company_name: string }>
> {
  const supabase = sb();
  const { data } = await supabase
    .from("stocks")
    .select("symbol, company_name")
    .eq("active", true)
    .order("symbol");
  return data ?? [];
}

export async function fetchStocks(
  nifty50Only = false
): Promise<StockWithPrice[]> {
  try {
    return await apiFetch<StockWithPrice[]>(
      `/stocks/live?nifty50_only=${nifty50Only ? "true" : "false"}`
    );
  } catch {
    // Fall back to DB-backed reads when the API is unavailable.
  }

  const supabase = sb();

  // 1. Fetch active stocks (optionally filtered to Nifty 50)
  let query = supabase
    .from("stocks")
    .select("symbol, company_name, sector, is_nifty50")
    .eq("active", true);
  if (nifty50Only) {
    query = query.eq("is_nifty50", true);
  }
  const { data: stocks, error: stocksErr } = await query.order("symbol");

  if (stocksErr || !stocks) return [];

  // 2. Fetch latest 2 ohlcv rows per symbol to compute price + change
  //    We fetch all recent ohlcv sorted by date desc and pick top 2 per symbol in JS.
  const { data: ohlcvRows } = await supabase
    .from("ohlcv")
    .select("symbol, date, close")
    .order("date", { ascending: false })
    .limit(200); // 50 stocks * ~2 rows each, with margin

  // 3. Fetch latest signals
  const { data: signalRows } = await supabase
    .from("signals")
    .select("symbol, signal, date")
    .order("date", { ascending: false })
    .limit(200);

  // Build lookup maps
  const ohlcvMap = new Map<string, number[]>();
  for (const row of ohlcvRows ?? []) {
    const arr = ohlcvMap.get(row.symbol) ?? [];
    if (arr.length < 2) {
      arr.push(row.close);
      ohlcvMap.set(row.symbol, arr);
    }
  }

  const signalMap = new Map<string, string>();
  for (const row of signalRows ?? []) {
    if (!signalMap.has(row.symbol)) {
      signalMap.set(row.symbol, row.signal);
    }
  }

  return stocks.map((s) => {
    const prices = ohlcvMap.get(s.symbol) ?? [];
    const currentPrice = prices[0] ?? 0;
    const prevPrice = prices[1] ?? currentPrice;
    const changePct =
      prevPrice !== 0 ? ((currentPrice - prevPrice) / prevPrice) * 100 : 0;

    return {
      symbol: s.symbol,
      company_name: s.company_name ?? "",
      sector: s.sector ?? "",
      current_price: currentPrice,
      change_pct: changePct,
      signal: signalMap.get(s.symbol),
    };
  });
}

export async function fetchStockDetail(
  symbol: string
): Promise<StockDetail | null> {
  try {
    return await apiFetch<StockDetail | null>(`/stocks/${encodeURIComponent(symbol)}/quote`);
  } catch {
    // Fall back to DB-backed reads when the live API is unavailable.
  }

  const supabase = sb();

  const { data: stock } = await supabase
    .from("stocks")
    .select("symbol, company_name, sector, market_cap_category")
    .eq("symbol", symbol)
    .single();

  if (!stock) return null;

  const { data: ohlcvRows } = await supabase
    .from("ohlcv")
    .select("date, open, high, low, close, volume")
    .eq("symbol", symbol)
    .order("date", { ascending: false })
    .limit(2);

  const latest = ohlcvRows?.[0];
  const prev = ohlcvRows?.[1];

  const currentPrice = latest?.close ?? 0;
  const prevClose = prev?.close ?? currentPrice;
  const change = currentPrice - prevClose;
  const changePct = prevClose !== 0 ? (change / prevClose) * 100 : 0;

  return {
    symbol: stock.symbol,
    company_name: stock.company_name ?? "",
    sector: stock.sector ?? "",
    current_price: currentPrice,
    change_pct: changePct,
    change,
    day_high: latest?.high ?? 0,
    day_low: latest?.low ?? 0,
    volume: latest?.volume ?? 0,
    market_cap: 0, // not stored in stocks table directly
  };
}

export interface OhlcvCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export async function fetchOhlcv(
  symbol: string,
  days = 365
): Promise<OhlcvCandle[]> {
  try {
    const data = await apiFetch<
      Array<{ date: string; open: number; high: number; low: number; close: number; volume: number }>
    >(`/stocks/${encodeURIComponent(symbol)}/ohlcv?days=${days}`);
    return (data ?? []).map((r) => ({
      time: r.date,
      open: r.open,
      high: r.high,
      low: r.low,
      close: r.close,
      volume: r.volume,
    }));
  } catch {
    // Fall back to DB-backed reads when the live API is unavailable.
  }

  const supabase = sb();
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - days);

  const { data } = await supabase
    .from("ohlcv")
    .select("date, open, high, low, close, volume")
    .eq("symbol", symbol)
    .gte("date", fromDate.toISOString().split("T")[0])
    .order("date", { ascending: true });

  return (data ?? []).map((r) => ({
    time: r.date,
    open: r.open,
    high: r.high,
    low: r.low,
    close: r.close,
    volume: r.volume,
  }));
}

export interface Indicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  sma_20: number;
  sma_50: number;
  ema_12: number;
  ema_26: number;
}

export async function fetchIndicators(
  symbol: string
): Promise<Indicators | null> {
  const supabase = sb();

  const { data } = await supabase
    .from("technical_indicators")
    .select("*")
    .eq("symbol", symbol)
    .order("date", { ascending: false })
    .limit(1)
    .single();

  if (!data) return null;

  return {
    rsi: data.rsi_14 ?? 0,
    macd: data.macd ?? 0,
    macd_signal: data.macd_signal ?? 0,
    macd_hist: data.macd_hist ?? 0,
    bb_upper: data.bb_upper ?? 0,
    bb_middle: data.bb_middle ?? 0,
    bb_lower: data.bb_lower ?? 0,
    sma_20: data.sma_20 ?? 0,
    sma_50: data.sma_50 ?? 0,
    ema_12: data.ema_12 ?? 0,
    ema_26: data.ema_26 ?? 0,
  };
}

export interface SentimentResult {
  overall: string;
  score: number;
  positive: number;
  negative: number;
  neutral: number;
}

export async function fetchStockSentiment(
  symbol: string
): Promise<SentimentResult | null> {
  const supabase = sb();

  const { data } = await supabase
    .from("sentiment_daily")
    .select("*")
    .eq("symbol", symbol)
    .order("date", { ascending: false })
    .limit(1)
    .single();

  if (!data) return null;

  const avgSentiment = data.avg_sentiment ?? 0;
  const overall =
    avgSentiment > 0.1 ? "positive" : avgSentiment < -0.1 ? "negative" : "neutral";

  return {
    overall,
    score: avgSentiment,
    positive: data.positive_avg ?? 0,
    negative: data.negative_avg ?? 0,
    neutral: data.neutral_avg ?? 0,
  };
}

export interface NewsItem {
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: string;
}

export async function fetchStockNews(
  symbol: string,
  limit = 20
): Promise<NewsItem[]> {
  const supabase = sb();

  const { data } = await supabase
    .from("article_sentiments")
    .select(
      "sentiment_label, news_articles!inner(title, source, url, published_at)"
    )
    .eq("symbol", symbol)
    .order("computed_at", { ascending: false })
    .limit(limit);

  if (!data) return [];

  return data.map((row) => {
    const article = row.news_articles as unknown as {
      title: string;
      source: string;
      url: string;
      published_at: string;
    };
    return {
      title: article.title ?? "",
      source: article.source ?? "",
      url: article.url ?? "",
      published_at: article.published_at ?? "",
      sentiment: row.sentiment_label ?? "neutral",
    };
  });
}

// ---------- Signals ----------

export interface SignalRow {
  symbol: string;
  signal: string;
  confidence: number;
  technical_score: number;
  sentiment_score: number;
  momentum_score: number;
  created_at: string;
  date: string;
}

export async function fetchSignals(): Promise<SignalRow[]> {
  const supabase = sb();

  // Fetch latest signals, order by date desc then symbol
  const { data } = await supabase
    .from("signals")
    .select("symbol, signal, confidence, technical_score, sentiment_score, momentum_score, date")
    .order("date", { ascending: false })
    .limit(200);

  if (!data) return [];

  // Deduplicate: keep only the latest per symbol
  const seen = new Set<string>();
  const result: SignalRow[] = [];
  for (const row of data) {
    if (!seen.has(row.symbol)) {
      seen.add(row.symbol);
      result.push({
        symbol: row.symbol,
        signal: row.signal,
        confidence: row.confidence ?? 0,
        technical_score: row.technical_score ?? 0,
        sentiment_score: row.sentiment_score ?? 0,
        momentum_score: row.momentum_score ?? 0,
        created_at: row.date,
        date: row.date,
      });
    }
  }
  return result;
}

export interface SignalSummary {
  strong_buy: number;
  buy: number;
  hold: number;
  sell: number;
  strong_sell: number;
  total: number;
}

export async function fetchSignalsSummary(): Promise<SignalSummary> {
  const signals = await fetchSignals();
  const summary: SignalSummary = {
    strong_buy: 0,
    buy: 0,
    hold: 0,
    sell: 0,
    strong_sell: 0,
    total: signals.length,
  };
  for (const s of signals) {
    const key = s.signal as keyof Omit<SignalSummary, "total">;
    if (key in summary) {
      summary[key]++;
    }
  }
  return summary;
}

export async function fetchLatestSignal(
  symbol: string
): Promise<SignalRow | null> {
  const supabase = sb();

  const { data } = await supabase
    .from("signals")
    .select("symbol, signal, confidence, technical_score, sentiment_score, momentum_score, date")
    .eq("symbol", symbol)
    .order("date", { ascending: false })
    .limit(1)
    .single();

  if (!data) return null;

  return {
    symbol: data.symbol,
    signal: data.signal,
    confidence: data.confidence ?? 0,
    technical_score: data.technical_score ?? 0,
    sentiment_score: data.sentiment_score ?? 0,
    momentum_score: data.momentum_score ?? 0,
    created_at: data.date,
    date: data.date,
  };
}

// ---------- Market ----------

export interface MarketSentiment {
  overall_sentiment: string;
  score: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
}

export async function fetchMarketSentiment(): Promise<MarketSentiment | null> {
  const supabase = sb();

  // Get the latest date with sentiment data
  const { data: latestRow } = await supabase
    .from("sentiment_daily")
    .select("date")
    .order("date", { ascending: false })
    .limit(1)
    .single();

  if (!latestRow) return null;

  const { data } = await supabase
    .from("sentiment_daily")
    .select("avg_sentiment")
    .eq("date", latestRow.date);

  if (!data || data.length === 0) return null;

  let bullish = 0;
  let bearish = 0;
  let neutral = 0;
  let total = 0;

  for (const row of data) {
    const s = row.avg_sentiment ?? 0;
    total += s;
    if (s > 0.1) bullish++;
    else if (s < -0.1) bearish++;
    else neutral++;
  }

  const avg = data.length > 0 ? total / data.length : 0;
  const overall =
    avg > 0.05 ? "bullish" : avg < -0.05 ? "bearish" : "neutral";

  return {
    overall_sentiment: overall,
    score: avg,
    bullish_count: bullish,
    bearish_count: bearish,
    neutral_count: neutral,
  };
}

export interface MarketOverview {
  nifty50_value: number;
  nifty50_change: number;
  nifty50_change_pct: number;
}

export async function fetchMarketOverview(): Promise<MarketOverview | null> {
  try {
    return await apiFetch<MarketOverview | null>("/market/index-overview");
  } catch {
    // Fall back to DB-backed reads when the live API is unavailable.
  }

  const supabase = sb();

  // Try ^NSEI (Nifty 50 index) in ohlcv
  const { data } = await supabase
    .from("ohlcv")
    .select("close, date")
    .eq("symbol", "^NSEI")
    .order("date", { ascending: false })
    .limit(2);

  if (!data || data.length === 0) return null;

  const latest = data[0].close;
  const prev = data[1]?.close ?? latest;
  const change = latest - prev;
  const changePct = prev !== 0 ? (change / prev) * 100 : 0;

  return {
    nifty50_value: latest,
    nifty50_change: change,
    nifty50_change_pct: changePct,
  };
}

// ---------- Portfolio (user-owned, RLS handles auth) ----------

export interface HoldingRow {
  id: string;
  symbol: string;
  quantity: number;
  avg_buy_price: number;
  buy_date: string;
  notes: string | null;
}

export interface HoldingWithPrice {
  id: string;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  value: number;
}

export async function fetchHoldingSymbols(): Promise<string[]> {
  const supabase = sb();
  const { data } = await supabase.from("holdings").select("symbol");
  return (data ?? []).map((holding) => holding.symbol);
}

export interface PortfolioPerformance {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_pct: number;
}

export async function fetchHoldings(): Promise<HoldingWithPrice[]> {
  try {
    return await apiFetch<HoldingWithPrice[]>("/holdings/live");
  } catch {
    // Fall back to DB-backed reads when the live API is unavailable.
  }

  const supabase = sb();

  const { data: holdings } = await supabase
    .from("holdings")
    .select("id, symbol, quantity, avg_buy_price, buy_date, notes");

  if (!holdings || holdings.length === 0) return [];

  // Fetch latest prices
  const symbols = [...new Set(holdings.map((h) => h.symbol))];
  const { data: ohlcvRows } = await supabase
    .from("ohlcv")
    .select("symbol, close, date")
    .in("symbol", symbols)
    .order("date", { ascending: false })
    .limit(symbols.length * 2);

  const priceMap = new Map<string, number>();
  for (const row of ohlcvRows ?? []) {
    if (!priceMap.has(row.symbol)) {
      priceMap.set(row.symbol, row.close);
    }
  }

  return holdings.map((h) => {
    const currentPrice = priceMap.get(h.symbol) ?? 0;
    const avgPrice = h.avg_buy_price ?? 0;
    const value = currentPrice * h.quantity;
    const invested = avgPrice * h.quantity;
    const pnl = value - invested;
    const pnlPct = invested !== 0 ? (pnl / invested) * 100 : 0;

    return {
      id: h.id,
      symbol: h.symbol,
      quantity: h.quantity,
      avg_price: avgPrice,
      current_price: currentPrice,
      pnl,
      pnl_pct: pnlPct,
      value,
    };
  });
}

export async function fetchPortfolioPerformance(): Promise<PortfolioPerformance | null> {
  const holdings = await fetchHoldings();
  if (holdings.length === 0) return null;

  const totalValue = holdings.reduce((sum, h) => sum + h.value, 0);
  const totalInvested = holdings.reduce(
    (sum, h) => sum + h.avg_price * h.quantity,
    0
  );
  const totalPnl = totalValue - totalInvested;
  const totalPnlPct = totalInvested !== 0 ? (totalPnl / totalInvested) * 100 : 0;

  return {
    total_value: totalValue,
    total_invested: totalInvested,
    total_pnl: totalPnl,
    total_pnl_pct: totalPnlPct,
  };
}

export async function addHolding(data: {
  symbol: string;
  quantity: number;
  avg_buy_price: number;
  buy_date?: string;
}) {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  const { error } = await supabase.from("holdings").insert({
    user_id: user.id,
    symbol: data.symbol,
    quantity: data.quantity,
    avg_buy_price: data.avg_buy_price,
    buy_date: data.buy_date ?? new Date().toISOString().split("T")[0],
  });

  if (error) throw new Error(error.message);
}

export async function deleteHolding(id: string) {
  const supabase = sb();
  const { error } = await supabase.from("holdings").delete().eq("id", id);
  if (error) throw new Error(error.message);
}

// ---------- Watchlist ----------

export interface WatchlistItemWithPrice {
  symbol: string;
  company_name: string;
  current_price: number;
  change_pct: number;
}

export async function fetchWatchlist(): Promise<WatchlistItemWithPrice[]> {
  try {
    return await apiFetch<WatchlistItemWithPrice[]>("/watchlist/live");
  } catch {
    // Fall back to DB-backed reads when the live API is unavailable.
  }

  const supabase = sb();

  const { data: wl } = await supabase
    .from("watchlist")
    .select("symbol, stocks(company_name)")
    .order("added_at", { ascending: false });

  if (!wl || wl.length === 0) return [];

  const symbols = wl.map((w) => w.symbol);

  const { data: ohlcvRows } = await supabase
    .from("ohlcv")
    .select("symbol, close, date")
    .in("symbol", symbols)
    .order("date", { ascending: false })
    .limit(symbols.length * 2);

  const priceMap = new Map<string, number[]>();
  for (const row of ohlcvRows ?? []) {
    const arr = priceMap.get(row.symbol) ?? [];
    if (arr.length < 2) {
      arr.push(row.close);
      priceMap.set(row.symbol, arr);
    }
  }

  return wl.map((w) => {
    const stockInfo = w.stocks as unknown as { company_name: string } | null;
    const prices = priceMap.get(w.symbol) ?? [];
    const currentPrice = prices[0] ?? 0;
    const prevPrice = prices[1] ?? currentPrice;
    const changePct =
      prevPrice !== 0 ? ((currentPrice - prevPrice) / prevPrice) * 100 : 0;

    return {
      symbol: w.symbol,
      company_name: stockInfo?.company_name ?? "",
      current_price: currentPrice,
      change_pct: changePct,
    };
  });
}

export async function fetchWatchlistSymbols(): Promise<string[]> {
  const supabase = sb();
  const { data } = await supabase.from("watchlist").select("symbol");
  return (data ?? []).map((w) => w.symbol);
}

export async function addToWatchlist(symbol: string) {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  const { error } = await supabase
    .from("watchlist")
    .insert({ user_id: user.id, symbol });

  if (error) throw new Error(error.message);
}

export async function removeFromWatchlist(symbol: string) {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  const { error } = await supabase
    .from("watchlist")
    .delete()
    .eq("user_id", user.id)
    .eq("symbol", symbol);

  if (error) throw new Error(error.message);
}

// ---------- Profile ----------

export interface Profile {
  email: string;
  full_name: string;
  risk_profile: string;
  risk_score: number;
  volatility_tolerance: number | null;
  time_horizon_score: number | null;
  knowledge_score: number | null;
  investable_surplus_range: string | null;
  email_notifications_enabled: boolean;
}

export async function fetchProfile(): Promise<Profile | null> {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;

  const { data } = await supabase
    .from("profiles")
    .select(
      "email, full_name, risk_profile, risk_score, volatility_tolerance, time_horizon_score, knowledge_score, investable_surplus_range, email_notifications_enabled"
    )
    .eq("id", user.id)
    .single();

  if (!data) return null;

  return {
    email: data.email ?? user.email ?? "",
    full_name: data.full_name ?? "",
    risk_profile: data.risk_profile ?? "",
    risk_score: data.risk_score ?? 0,
    volatility_tolerance: data.volatility_tolerance ?? null,
    time_horizon_score: data.time_horizon_score ?? null,
    knowledge_score: data.knowledge_score ?? null,
    investable_surplus_range: data.investable_surplus_range ?? null,
    email_notifications_enabled: data.email_notifications_enabled ?? false,
  };
}

export async function updateProfile(updates: Partial<Profile>) {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  const { error } = await supabase
    .from("profiles")
    .update(updates)
    .eq("id", user.id);

  if (error) throw new Error(error.message);
}

// ---------- Alerts ----------

export interface AlertRow {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export async function fetchAlerts(limit = 50): Promise<AlertRow[]> {
  const supabase = sb();

  const { data } = await supabase
    .from("alerts")
    .select("id, title, message, is_read, created_at")
    .order("created_at", { ascending: false })
    .limit(limit);

  return data ?? [];
}

export async function markAlertRead(id: string) {
  const supabase = sb();
  const { error } = await supabase
    .from("alerts")
    .update({ is_read: true })
    .eq("id", id);
  if (error) throw new Error(error.message);
}

export async function markAllAlertsRead() {
  const supabase = sb();
  const { error } = await supabase
    .from("alerts")
    .update({ is_read: true })
    .eq("is_read", false);
  if (error) throw new Error(error.message);
}

// ---------- Signal Acceptance ----------

export interface AcceptedSignal {
  id: string;
  symbol: string;
  signal_type: string;
  signal_date: string;
  composite_score: number | null;
  status: string;
  accepted_at: string;
}

export async function acceptSignal(data: {
  symbol: string;
  signal_type: string;
  signal_date: string;
  composite_score?: number;
}): Promise<void> {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  // 1. Insert into accepted_signals
  const { error: acceptError } = await supabase.from("accepted_signals").insert({
    user_id: user.id,
    symbol: data.symbol,
    signal_type: data.signal_type,
    signal_date: data.signal_date,
    composite_score: data.composite_score ?? null,
    status: "active",
  });
  if (acceptError) throw new Error(acceptError.message);

  // 2. Upsert into signal_notifications for email tracking
  const { error: notifError } = await supabase
    .from("signal_notifications")
    .upsert(
      {
        user_id: user.id,
        symbol: data.symbol,
        last_signal: data.signal_type,
        is_active: true,
      },
      { onConflict: "user_id,symbol" }
    );
  if (notifError) {
    console.error("Failed to create signal notification tracking:", notifError.message);
  }
}

export async function fetchAcceptedSignals(): Promise<AcceptedSignal[]> {
  const supabase = sb();

  const { data } = await supabase
    .from("accepted_signals")
    .select("id, symbol, signal_type, signal_date, composite_score, status, accepted_at")
    .eq("status", "active")
    .order("accepted_at", { ascending: false })
    .limit(100);

  return data ?? [];
}

export async function cancelAcceptedSignal(id: string): Promise<void> {
  const supabase = sb();
  const { error } = await supabase
    .from("accepted_signals")
    .update({ status: "cancelled" })
    .eq("id", id);
  if (error) throw new Error(error.message);
}

// ---------- Portfolio Optimization ----------

export interface OptimizationAllocation {
  symbol: string;
  current_weight: number;
  recommended_weight: number;
  weight_change: number;
  action: string;
}

export interface OptimizationResult {
  id: string;
  optimization_method: string;
  expected_return: number | null;
  expected_risk: number | null;
  sharpe_ratio: number | null;
  allocations: OptimizationAllocation[];
}

function isOptimizationResult(value: unknown): value is OptimizationResult {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<OptimizationResult>;
  return Array.isArray(candidate.allocations) && candidate.allocations.length > 0;
}

// Local JS implementation used as a fallback when the Python ML backend
// (PyPortfolioOpt) is not available. We keep this logic in a helper so the
// exported `runOptimization` can prefer the server when available.
export async function runOptimizationLocal(): Promise<OptimizationResult | null> {
  const supabase = sb();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  // Get user's risk profile
  const { data: profile } = await supabase
    .from("profiles")
    .select("risk_profile")
    .eq("id", user.id)
    .single();

  const riskProfile = profile?.risk_profile ?? "moderate";

  // Get holdings
  const { data: holdings } = await supabase
    .from("holdings")
    .select("symbol, quantity, avg_buy_price");

  if (!holdings || holdings.length === 0) throw new Error("No holdings to optimize");

  const symbols = [...new Set(holdings.map((h) => h.symbol))];

  // Fetch OHLCV for computing returns
  const { data: ohlcvData } = await supabase
    .from("ohlcv")
    .select("symbol, date, close")
    .in("symbol", symbols)
    .order("date", { ascending: true });

  // Fetch latest signals
  const { data: signalData } = await supabase
    .from("signals")
    .select("symbol, signal, confidence, technical_score, momentum_score")
    .in("symbol", symbols)
    .order("date", { ascending: false })
    .limit(symbols.length * 2);

  // Build price series per symbol
  const priceMap = new Map<string, number[]>();
  for (const row of ohlcvData ?? []) {
    const arr = priceMap.get(row.symbol) ?? [];
    arr.push(row.close);
    priceMap.set(row.symbol, arr);
  }

  // Latest signal per symbol
  const signalMap = new Map<string, { signal: string }>();
  for (const row of signalData ?? []) {
    if (!signalMap.has(row.symbol)) {
      signalMap.set(row.symbol, { signal: row.signal });
    }
  }

  // Compute metrics per symbol
  const metrics: Array<{ symbol: string; avgReturn: number; volatility: number; signalScore: number }> = [];
  for (const sym of symbols) {
    const prices = priceMap.get(sym) ?? [];
    let avgReturn = 0;
    let volatility = 0.2;
    if (prices.length >= 20) {
      const returns: number[] = [];
      for (let i = 1; i < prices.length; i++) {
        returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
      }
      avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length * 252;
      const mean = avgReturn / 252;
      volatility = Math.sqrt(
        returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length * 252
      );
    }

    const sig = signalMap.get(sym);
    const signalWeight: Record<string, number> = {
      strong_buy: 1, buy: 0.5, hold: 0, sell: -0.5, strong_sell: -1,
    };
    const signalScore = sig ? (signalWeight[sig.signal] ?? 0) : 0;
    metrics.push({ symbol: sym, avgReturn, volatility, signalScore });
  }

  // Compute scores based on risk profile
  const scores = new Map<string, number>();
  for (const m of metrics) {
    let score: number;
    if (riskProfile === "conservative") {
      score = Math.max(0.01, 1 / (m.volatility + 0.01) + m.signalScore * 0.3);
    } else if (riskProfile === "aggressive") {
      score = Math.max(0.01, m.avgReturn + m.signalScore * 0.5);
    } else {
      score = Math.max(0.01, m.avgReturn * 0.5 + (1 / (m.volatility + 0.01)) * 0.3 + m.signalScore * 0.2);
    }
    scores.set(m.symbol, score);
  }

  const totalScore = [...scores.values()].reduce((a, b) => a + b, 0);

  // Current portfolio values
  const latestPrices = new Map<string, number>();
  for (const sym of symbols) {
    const prices = priceMap.get(sym) ?? [];
    latestPrices.set(sym, prices[prices.length - 1] ?? 0);
  }

  let totalValue = 0;
  const currentValues = new Map<string, number>();
  for (const h of holdings) {
    const price = latestPrices.get(h.symbol) ?? h.avg_buy_price;
    const val = h.quantity * price;
    currentValues.set(h.symbol, (currentValues.get(h.symbol) ?? 0) + val);
    totalValue += val;
  }

  const allocations: OptimizationAllocation[] = symbols.map((sym) => {
    const currentVal = currentValues.get(sym) ?? 0;
    const cw = totalValue > 0 ? currentVal / totalValue : 0;
    const rw = totalScore > 0 ? (scores.get(sym) ?? 0) / totalScore : 1 / symbols.length;
    const wc = rw - cw;
    const action = wc > 0.02 ? "buy" : wc < -0.02 ? "sell" : "hold";
    return {
      symbol: sym,
      current_weight: Math.round(cw * 10000) / 10000,
      recommended_weight: Math.round(rw * 10000) / 10000,
      weight_change: Math.round(wc * 10000) / 10000,
      action,
    };
  });

  // Portfolio-level stats
  const avgReturn = metrics.reduce((s, m) => {
    const w = (scores.get(m.symbol) ?? 0) / (totalScore || 1);
    return s + w * m.avgReturn;
  }, 0);
  const avgVol = metrics.reduce((s, m) => {
    const w = (scores.get(m.symbol) ?? 0) / (totalScore || 1);
    return s + w * m.volatility;
  }, 0);
  const sharpe = avgVol > 0 ? (avgReturn - 0.07) / avgVol : 0;

  const methodMap: Record<string, string> = {
    conservative: "min_volatility",
    moderate: "max_sharpe",
    aggressive: "efficient_return",
  };

  // Save to DB (column names must match migration 005 schema)
  const { data: optRow, error: optError } = await supabase
    .from("portfolio_optimizations")
    .insert({
      user_id: user.id,
      risk_profile: riskProfile,
      optimization_method: methodMap[riskProfile] ?? "max_sharpe",
      expected_return: Math.round(avgReturn * 10000) / 10000,
      expected_risk: Math.round(avgVol * 10000) / 10000,
      sharpe_ratio: Math.round(sharpe * 10000) / 10000,
      status: "completed",
    })
    .select("id")
    .single();

  if (optError) {
    console.error("Failed to save optimization:", optError.message);
  }

  if (optRow) {
    const allocRows = allocations.map((a) => ({
      optimization_id: optRow.id,
      symbol: a.symbol,
      current_weight: a.current_weight,
      recommended_weight: a.recommended_weight,
      current_value: Math.round(a.current_weight * totalValue * 100) / 100,
      recommended_value: Math.round(a.recommended_weight * totalValue * 100) / 100,
    }));
    await supabase.from("optimization_allocations").insert(allocRows);
  }

  return {
    id: optRow?.id ?? "local",
    optimization_method: methodMap[riskProfile] ?? "max_sharpe",
    expected_return: Math.round(avgReturn * 10000) / 10000,
    expected_risk: Math.round(avgVol * 10000) / 10000,
    sharpe_ratio: Math.round(sharpe * 10000) / 10000,
    allocations,
  };
}

// Run portfolio optimization. Uses the local JS optimizer as the primary path
// since the Python ML backend may not be running. If the FastAPI server is
// available AND returns a full result with allocations, use that instead.
export async function runOptimization(): Promise<OptimizationResult | null> {
  // Try the server endpoint first — it may run PyPortfolioOpt inline
  try {
    const serverRes = await apiFetch<Record<string, unknown>>(
      "/portfolio/optimize",
      { method: "POST", body: JSON.stringify({}) }
    );

    // If server returned a full optimization result with allocations, use it
    if (isOptimizationResult(serverRes)) {
      return serverRes;
    }
  } catch {
    // Server not reachable — fall through to local optimizer
  }

  // Primary path: local JS optimizer (always available)
  return await runOptimizationLocal();
}
