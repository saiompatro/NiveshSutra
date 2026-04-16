import type { SupabaseClient } from "@supabase/supabase-js";

const DEFAULT_CACHE_TTL_SECONDS = 60;
const DEFAULT_INSTRUMENT_CACHE_TTL_SECONDS = 60 * 60 * 24;

type Primitive = string | number | boolean | null;
type CandleValue = string | number | null;

interface UpstoxQuoteEntry {
  ohlc?: Partial<Record<"open" | "high" | "low" | "close", number | string | null>>;
  last_price?: number | string | null;
  net_change?: number | string | null;
  timestamp?: string | null;
  last_trade_time?: string | null;
  volume?: number | string | null;
}

interface HistoricalPayload {
  candles?: CandleValue[][];
}

interface DbBar {
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface QuoteSnapshot {
  providerSymbol: string;
  price: number;
  previousClose: number;
  change: number;
  changePct: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  latestTradingDay: string;
  provider: "upstox" | "supabase";
}

export interface HistoryBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface InstrumentMeta {
  symbol: string;
  instrumentKey: string;
  exchange: string;
  segment: string;
  tradingSymbol: string;
  name: string;
  shortName: string;
  preferredTicker?: string | null;
}

interface UpstoxResponse<T> {
  status?: string;
  data?: T;
  errors?: Array<{ errorCode?: string; message?: string }>;
}

const quoteCache = new Map<string, { storedAt: number; value: QuoteSnapshot }>();
const instrumentCache = new Map<string, { storedAt: number; value: InstrumentMeta }>();

function nowMs() {
  return Date.now();
}

function cacheTtlMs() {
  const ttl = Number(process.env.MARKET_DATA_CACHE_TTL_SECONDS ?? DEFAULT_CACHE_TTL_SECONDS);
  return Math.max(10, Number.isFinite(ttl) ? ttl : DEFAULT_CACHE_TTL_SECONDS) * 1000;
}

function instrumentCacheTtlMs() {
  return DEFAULT_INSTRUMENT_CACHE_TTL_SECONDS * 1000;
}

function baseUrl() {
  return (process.env.UPSTOX_BASE_URL ?? "https://api.upstox.com/v2").replace(/\/+$/, "");
}

function accessToken() {
  const token = process.env.UPSTOX_ACCESS_TOKEN ?? "";
  if (!token) {
    throw new Error("UPSTOX_ACCESS_TOKEN is not configured");
  }
  return token;
}

function upstoxHeaders() {
  return {
    Accept: "application/json",
    Authorization: `Bearer ${accessToken()}`,
    "Content-Type": "application/json",
  };
}

function normalizeSymbol(input: string) {
  return input
    .trim()
    .toUpperCase()
    .replace(/\.(NS|NSE|BO|BSE)$/g, "");
}

function cacheKey(symbol: string, preferredTicker?: string | null) {
  return `${normalizeSymbol(symbol)}::${(preferredTicker ?? "").trim().toUpperCase()}`;
}

function preferredExchanges(preferredTicker?: string | null) {
  const normalized = (preferredTicker ?? "").trim().toUpperCase();
  if (normalized.endsWith(".NS")) return ["NSE", "BSE"];
  if (normalized.endsWith(".BO") || normalized.endsWith(".BSE")) return ["BSE", "NSE"];
  return ["NSE", "BSE"];
}

function queryCandidates(rawQuery: string) {
  const normalized = normalizeSymbol(rawQuery);
  if (normalized === "^NSEI") {
    return ["NIFTY 50", "NIFTY"];
  }

  const trimmed = rawQuery.trim();
  return Array.from(new Set([trimmed, normalized].filter(Boolean)));
}

function normalizeInstrument(row: Record<string, Primitive>, fallbackSymbol: string, preferredTicker?: string | null): InstrumentMeta | null {
  const instrumentKey = String(row.instrument_key ?? row.instrument_token ?? row.instrumentKey ?? "");
  if (!instrumentKey) return null;

  const exchange = String(row.exchange ?? instrumentKey.split("|", 1)[0] ?? "");
  const segment = String(row.segment ?? "");
  const tradingSymbol = String(
    row.trading_symbol ?? row.symbol ?? row.tradingsymbol ?? fallbackSymbol
  );

  return {
    symbol: fallbackSymbol,
    instrumentKey,
    exchange,
    segment,
    tradingSymbol,
    name: String(row.name ?? tradingSymbol),
    shortName: String(row.short_name ?? row.shortName ?? row.name ?? tradingSymbol),
    preferredTicker,
  };
}

function scoreInstrument(
  row: Record<string, Primitive>,
  normalizedQuery: string,
  rawQuery: string,
  exchangeOrder: string[]
) {
  const tradingSymbol = String(
    row.trading_symbol ?? row.symbol ?? row.tradingsymbol ?? ""
  ).toUpperCase();
  const shortName = String(row.short_name ?? row.shortName ?? "").toUpperCase();
  const name = String(row.name ?? "").toUpperCase();
  const exchange = String(row.exchange ?? "").toUpperCase();
  const segment = String(row.segment ?? "").toUpperCase();
  const haystack = `${tradingSymbol} ${shortName} ${name}`;
  const rawUpper = rawQuery.trim().toUpperCase();

  let score = 0;
  if (normalizedQuery === "^NSEI") {
    if (segment.endsWith("INDEX") || String(row.instrument_type ?? "").toUpperCase() === "INDEX") {
      score += 100;
    }
    if (tradingSymbol === "NIFTY" || name.includes("NIFTY 50")) {
      score += 200;
    }
  } else {
    if (segment.endsWith("EQ") || String(row.instrument_type ?? "").toUpperCase() === "A") {
      score += 80;
    }
    if (tradingSymbol === normalizedQuery) score += 200;
    else if (tradingSymbol.startsWith(normalizedQuery)) score += 120;
    else if (shortName === normalizedQuery) score += 90;
  }

  if (rawUpper && haystack.includes(rawUpper)) score += 40;
  if (normalizedQuery && haystack.includes(normalizedQuery)) score += 25;

  const exchangeIndex = exchangeOrder.indexOf(exchange);
  if (exchangeIndex === 0) score += 20;
  else if (exchangeIndex === 1) score += 10;

  return score;
}

async function upstoxGet<T>(path: string, params?: Record<string, Primitive>) {
  const url = new URL(`${baseUrl()}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }

  const response = await fetch(url, {
    headers: upstoxHeaders(),
    cache: "no-store",
  });

  const payload = (await response.json().catch(() => ({}))) as UpstoxResponse<T>;
  if (!response.ok) {
    const message = payload.errors?.[0]?.message ?? `Upstox request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

function getCachedQuote(symbol: string, preferredTicker?: string | null) {
  const cached = quoteCache.get(cacheKey(symbol, preferredTicker));
  if (!cached) return null;
  if (nowMs() - cached.storedAt > cacheTtlMs()) {
    quoteCache.delete(cacheKey(symbol, preferredTicker));
    return null;
  }
  return cached.value;
}

function setCachedQuote(symbol: string, quote: QuoteSnapshot, preferredTicker?: string | null) {
  quoteCache.set(cacheKey(symbol, preferredTicker), { storedAt: nowMs(), value: quote });
  return quote;
}

function getCachedInstrument(symbol: string, preferredTicker?: string | null) {
  const cached = instrumentCache.get(cacheKey(symbol, preferredTicker));
  if (!cached) return null;
  if (nowMs() - cached.storedAt > instrumentCacheTtlMs()) {
    instrumentCache.delete(cacheKey(symbol, preferredTicker));
    return null;
  }
  return cached.value;
}

function setCachedInstrument(symbol: string, instrument: InstrumentMeta, preferredTicker?: string | null) {
  instrumentCache.set(cacheKey(symbol, preferredTicker), { storedAt: nowMs(), value: instrument });
  return instrument;
}

export async function searchInstrument(query: string, preferredTicker?: string | null) {
  const normalized = normalizeSymbol(query);
  const cached = getCachedInstrument(normalized, preferredTicker);
  if (cached) return cached;

  const exchangeOrder = preferredExchanges(preferredTicker);
  let bestInstrument: InstrumentMeta | null = null;
  let bestScore = Number.NEGATIVE_INFINITY;

  for (const candidateQuery of queryCandidates(query)) {
    const payload = await upstoxGet<Array<Record<string, Primitive>>>("/instruments/search", {
      query: candidateQuery,
      exchanges: normalized === "^NSEI" ? "NSE,BSE" : exchangeOrder.join(","),
      segments: normalized === "^NSEI" ? "INDEX,EQ" : "EQ,INDEX",
      page_number: 1,
      records: 30,
    });

    for (const row of payload.data ?? []) {
      const instrument = normalizeInstrument(row, normalized, preferredTicker);
      if (!instrument) continue;
      const score = scoreInstrument(row, normalized, query, exchangeOrder);
      if (score > bestScore) {
        bestInstrument = instrument;
        bestScore = score;
      }
    }

    if (bestInstrument && bestScore >= 120) {
      return setCachedInstrument(normalized, bestInstrument, preferredTicker);
    }
  }

  if (bestInstrument) {
    return setCachedInstrument(normalized, bestInstrument, preferredTicker);
  }

  throw new Error(`Upstox instrument not found for ${normalized}`);
}

function quoteFromUpstoxEntry(entry: UpstoxQuoteEntry, meta: InstrumentMeta): QuoteSnapshot {
  const ohlc = entry.ohlc ?? {};
  const price = Number(entry.last_price ?? 0);
  const previousClose = Number(ohlc.close ?? 0);
  const change = Number(entry.net_change ?? price - previousClose);
  const timestamp = String(entry.timestamp ?? entry.last_trade_time ?? "");
  const latestTradingDay = timestamp.length >= 10 ? timestamp.slice(0, 10) : new Date().toISOString().slice(0, 10);

  return {
    providerSymbol: meta.tradingSymbol,
    price,
    previousClose,
    change,
    changePct: previousClose ? (change / previousClose) * 100 : 0,
    open: Number(ohlc.open ?? 0),
    high: Number(ohlc.high ?? 0),
    low: Number(ohlc.low ?? 0),
    volume: Number(entry.volume ?? 0),
    latestTradingDay,
    provider: "upstox",
  };
}

export async function fetchLiveQuotesBatch(requestsMap: Record<string, string | null | undefined>) {
  const result: Record<string, QuoteSnapshot> = {};
  const metas = new Map<string, InstrumentMeta>();

  await Promise.all(
    Object.entries(requestsMap).map(async ([symbol, preferredTicker]) => {
      const cached = getCachedQuote(symbol, preferredTicker);
      if (cached) {
        result[symbol] = cached;
        return;
      }

      try {
        metas.set(symbol, await searchInstrument(symbol, preferredTicker));
      } catch {
        // Ignore missing live matches and let callers fall back to DB data.
      }
    })
  );

  const instrumentKeys = Array.from(new Set(Array.from(metas.values()).map((meta) => meta.instrumentKey)));
  if (instrumentKeys.length === 0) return result;

  const payload = await upstoxGet<Record<string, UpstoxQuoteEntry>>("/market-quote/quotes", {
    instrument_key: instrumentKeys.join(","),
  });
  const data = payload.data ?? {};

  for (const [symbol, meta] of metas.entries()) {
    const entry = data[meta.instrumentKey];
    if (!entry) continue;
    result[symbol] = setCachedQuote(symbol, quoteFromUpstoxEntry(entry, meta), requestsMap[symbol]);
  }

  return result;
}

export async function fetchLiveQuote(symbol: string, preferredTicker?: string | null) {
  const cached = getCachedQuote(symbol, preferredTicker);
  if (cached) return cached;

  const quotes = await fetchLiveQuotesBatch({ [symbol]: preferredTicker });
  const quote = quotes[symbol];
  if (!quote) {
    throw new Error(`Upstox quote not found for ${normalizeSymbol(symbol)}`);
  }
  return quote;
}

export async function fetchHistoricalDaily(symbol: string, preferredTicker?: string | null, days = 365) {
  const instrument = await searchInstrument(symbol, preferredTicker);
  const toDate = new Date();
  const fromDate = new Date(toDate);
  fromDate.setDate(fromDate.getDate() - days);

  const payload = await upstoxGet<HistoricalPayload | CandleValue[][]>(
    `/historical-candle/${encodeURIComponent(instrument.instrumentKey)}/day/${toDate.toISOString().slice(0, 10)}/${fromDate.toISOString().slice(0, 10)}`
  );

  const rawCandles = Array.isArray(payload.data) ? payload.data : payload.data?.candles ?? [];
  return rawCandles
    .filter((candle) => Array.isArray(candle) && candle.length >= 6)
    .map((candle): HistoryBar => ({
      date: String(candle[0]).slice(0, 10),
      open: Number(candle[1]),
      high: Number(candle[2]),
      low: Number(candle[3]),
      close: Number(candle[4]),
      volume: Number(candle[5]),
    }))
    .sort((left, right) => left.date.localeCompare(right.date));
}

export async function getLatestDbBars(supabase: SupabaseClient, symbols: string[]) {
  if (symbols.length === 0) return {} as Record<string, DbBar[]>;

  const { data, error } = await supabase
    .from("ohlcv")
    .select("symbol, date, open, high, low, close, volume")
    .in("symbol", symbols)
    .order("date", { ascending: false })
    .limit(Math.max(6, symbols.length * 3));

  if (error) throw new Error(error.message);

  const grouped: Record<string, DbBar[]> = {};
  for (const row of data ?? []) {
    const items = grouped[row.symbol] ?? [];
    if (items.length < 2) {
      items.push(row);
      grouped[row.symbol] = items;
    }
  }
  return grouped;
}

export async function getQuoteWithFallback(
  supabase: SupabaseClient,
  symbol: string,
  preferredTicker?: string | null
) {
  try {
    return await fetchLiveQuote(symbol, preferredTicker);
  } catch {
    const rows = (await getLatestDbBars(supabase, [symbol]))[symbol] ?? [];
    if (rows.length === 0) {
      throw new Error(`No price data found for ${symbol}`);
    }

    const latest = rows[0];
    const previous = rows[1] ?? latest;
    const previousClose = Number(previous.close ?? latest.close ?? 0);
    const price = Number(latest.close ?? 0);
    const change = price - previousClose;

    return {
      providerSymbol: symbol,
      price,
      previousClose,
      change,
      changePct: previousClose ? (change / previousClose) * 100 : 0,
      open: Number(latest.open ?? 0),
      high: Number(latest.high ?? 0),
      low: Number(latest.low ?? 0),
      volume: Number(latest.volume ?? 0),
      latestTradingDay: String(latest.date ?? ""),
      provider: "supabase",
    } satisfies QuoteSnapshot;
  }
}

export function mergeLiveQuoteIntoHistory(history: HistoryBar[], quote: QuoteSnapshot): HistoryBar[] {
  if (history.length === 0) return history;

  const merged = history.map((item) => ({ ...item }));
  const targetDay = quote.latestTradingDay || new Date().toISOString().slice(0, 10);
  const last = merged[merged.length - 1];
  const liveBar = {
    date: targetDay,
    open: quote.open || Number(last.open),
    high: Math.max(Number(last.high), quote.high || quote.price),
    low: Math.min(Number(last.low), quote.low || quote.price),
    close: quote.price,
    volume: quote.volume || Number(last.volume),
  };

  if (String(last.date) === targetDay) {
    merged[merged.length - 1] = { ...last, ...liveBar };
  } else if (String(last.date) < targetDay) {
    merged.push(liveBar);
  }

  return merged;
}
