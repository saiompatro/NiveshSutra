import { createClient } from "@/lib/supabase";

// ── Legacy helper (deprecated — use named functions below) ──────────
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function fetchStocks(): Promise<StockWithPrice[]> {
  const supabase = sb();

  // 1. Fetch all active stocks
  const { data: stocks, error: stocksErr } = await supabase
    .from("stocks")
    .select("symbol, company_name, sector")
    .eq("active", true)
    .order("symbol");

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
    macd: data.macd_line ?? 0,
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

export interface PortfolioPerformance {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_pct: number;
}

export async function fetchHoldings(): Promise<HoldingWithPrice[]> {
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
}

export async function fetchProfile(): Promise<Profile | null> {
  const supabase = sb();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;

  const { data } = await supabase
    .from("profiles")
    .select("email, full_name, risk_profile, risk_score")
    .eq("id", user.id)
    .single();

  if (!data) return null;

  return {
    email: data.email ?? user.email ?? "",
    full_name: data.full_name ?? "",
    risk_profile: data.risk_profile ?? "",
    risk_score: data.risk_score ?? 0,
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

// ---------- Portfolio Optimization (stub — requires Python backend) ----------

export async function runOptimization(): Promise<null> {
  return null;
}
