import { NextRequest, NextResponse } from "next/server";

export interface LiveQuote {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  prev_close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  time: number;
  provider: string;
}

type BackendStockQuote = {
  symbol: string;
  current_price: number;
  change?: number;
  change_pct: number;
  previous_close?: number;
  day_high?: number;
  day_low?: number;
  volume?: number;
  provider?: string;
};

type BackendIndexQuote = {
  nifty50_value: number;
  nifty50_change: number;
  nifty50_change_pct: number;
  provider?: string;
};

const API_BASE =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

const CACHE_TTL_MS = 10_000;
let _cache: { data: LiveQuote[]; ts: number } | null = null;

function apiUrl(path: string) {
  return `${API_BASE.replace(/\/$/, "")}${path}`;
}

function splitSymbols(value: string | null) {
  return value
    ? value
        .split(",")
        .map((symbol) => symbol.trim().toUpperCase())
        .filter(Boolean)
    : [];
}

function mapStockQuote(row: BackendStockQuote): LiveQuote {
  const price = Number(row.current_price ?? 0);
  const change = Number(row.change ?? 0);
  const previousClose = Number(row.previous_close ?? price - change);
  return {
    symbol: row.symbol,
    price,
    change,
    change_pct: Number(row.change_pct ?? 0),
    prev_close: previousClose,
    open: price,
    high: Number(row.day_high ?? price),
    low: Number(row.day_low ?? price),
    volume: Number(row.volume ?? 0),
    time: Math.floor(Date.now() / 1000),
    provider: row.provider ?? "backend",
  };
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path), {
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return (await res.json()) as T;
}

async function fetchIndexQuote(): Promise<LiveQuote | null> {
  const data = await fetchJson<BackendIndexQuote | null>("/api/v1/market/index-overview");
  if (!data) return null;
  const price = Number(data.nifty50_value ?? 0);
  const change = Number(data.nifty50_change ?? 0);
  return {
    symbol: "^NSEI",
    price,
    change,
    change_pct: Number(data.nifty50_change_pct ?? 0),
    prev_close: price - change,
    open: price,
    high: price,
    low: price,
    volume: 0,
    time: Math.floor(Date.now() / 1000),
    provider: data.provider ?? "backend",
  };
}

async function fetchStockQuote(symbol: string): Promise<LiveQuote | null> {
  const data = await fetchJson<BackendStockQuote | null>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/quote`
  );
  return data ? mapStockQuote(data) : null;
}

async function fetchAllNiftyQuotes(): Promise<LiveQuote[]> {
  const data = await fetchJson<BackendStockQuote[]>(
    "/api/v1/stocks/live?nifty50_only=true"
  );
  return data.map(mapStockQuote);
}

export async function GET(req: NextRequest) {
  if (!API_BASE) {
    return NextResponse.json(
      { error: "API_BASE_URL or NEXT_PUBLIC_API_BASE_URL is required for live quotes" },
      { status: 503 }
    );
  }

  const symbols = splitSymbols(req.nextUrl.searchParams.get("symbols"));
  if (!symbols.length && _cache && Date.now() - _cache.ts < CACHE_TTL_MS) {
    return NextResponse.json(_cache.data, {
      headers: { "X-Cache": "HIT", "Cache-Control": "no-store" },
    });
  }

  try {
    let quotes: LiveQuote[];
    if (symbols.length) {
      const results = await Promise.all(
        symbols.map((symbol) =>
          symbol === "^NSEI" ? fetchIndexQuote() : fetchStockQuote(symbol)
        )
      );
      quotes = results.filter((quote): quote is LiveQuote => quote !== null);
    } else {
      quotes = await fetchAllNiftyQuotes();
      const indexQuote = await fetchIndexQuote();
      if (indexQuote) quotes.push(indexQuote);
      _cache = { data: quotes, ts: Date.now() };
    }

    return NextResponse.json(quotes, {
      headers: { "X-Cache": "MISS", "Cache-Control": "no-store" },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: "Failed to fetch live quotes", detail: msg },
      { status: 503 }
    );
  }
}
