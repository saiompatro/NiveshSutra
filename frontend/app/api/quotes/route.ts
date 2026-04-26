import { NextRequest, NextResponse } from "next/server";

// Nifty 50 tickers on Yahoo Finance (with .NS suffix)
// Matches the symbols stored in Supabase without suffix
const NIFTY50_TICKERS: Record<string, string> = {
  ADANIENT: "ADANIENT.NS",
  ADANIPORTS: "ADANIPORTS.NS",
  APOLLOHOSP: "APOLLOHOSP.NS",
  ASIANPAINT: "ASIANPAINT.NS",
  AXISBANK: "AXISBANK.NS",
  BAJAJ_AUTO: "BAJAJ-AUTO.NS",
  BAJAJFINSV: "BAJAJFINSV.NS",
  BAJFINANCE: "BAJFINANCE.NS",
  BHARTIARTL: "BHARTIARTL.NS",
  BPCL: "BPCL.NS",
  BRITANNIA: "BRITANNIA.NS",
  CIPLA: "CIPLA.NS",
  COALINDIA: "COALINDIA.NS",
  DIVISLAB: "DIVISLAB.NS",
  DRREDDY: "DRREDDY.NS",
  EICHERMOT: "EICHERMOT.NS",
  GRASIM: "GRASIM.NS",
  HCLTECH: "HCLTECH.NS",
  HDFCBANK: "HDFCBANK.NS",
  HDFCLIFE: "HDFCLIFE.NS",
  HEROMOTOCO: "HEROMOTOCO.NS",
  HINDALCO: "HINDALCO.NS",
  HINDUNILVR: "HINDUNILVR.NS",
  ICICIBANK: "ICICIBANK.NS",
  INDUSINDBK: "INDUSINDBK.NS",
  INFY: "INFY.NS",
  ITC: "ITC.NS",
  JSWSTEEL: "JSWSTEEL.NS",
  KOTAKBANK: "KOTAKBANK.NS",
  LT: "LT.NS",
  M_M: "M&M.NS",
  MARUTI: "MARUTI.NS",
  NESTLEIND: "NESTLEIND.NS",
  NTPC: "NTPC.NS",
  ONGC: "ONGC.NS",
  POWERGRID: "POWERGRID.NS",
  RELIANCE: "RELIANCE.NS",
  SBILIFE: "SBILIFE.NS",
  SBIN: "SBIN.NS",
  SUNPHARMA: "SUNPHARMA.NS",
  TATACONSUM: "TATACONSUM.NS",
  TATAMOTORS: "TATAMOTORS.NS",
  TATASTEEL: "TATASTEEL.NS",
  TCS: "TCS.NS",
  TECHM: "TECHM.NS",
  TITAN: "TITAN.NS",
  TRENT: "TRENT.NS",
  ULTRACEMCO: "ULTRACEMCO.NS",
  WIPRO: "WIPRO.NS",
  "^NSEI": "^NSEI",
};

const YF_FIELDS =
  "regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketPreviousClose,regularMarketOpen,regularMarketDayHigh,regularMarketDayLow,regularMarketVolume,regularMarketTime";

export interface LiveQuote {
  symbol: string;       // DB symbol (no .NS)
  price: number;
  change: number;
  change_pct: number;
  prev_close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  time: number;         // unix timestamp
  provider: "yahoo";
}

function mapResult(symbol: string, r: Record<string, unknown>): LiveQuote {
  return {
    symbol,
    price: Number(r.regularMarketPrice ?? 0),
    change: Number(r.regularMarketChange ?? 0),
    change_pct: Number(r.regularMarketChangePercent ?? 0),
    prev_close: Number(r.regularMarketPreviousClose ?? 0),
    open: Number(r.regularMarketOpen ?? 0),
    high: Number(r.regularMarketDayHigh ?? 0),
    low: Number(r.regularMarketDayLow ?? 0),
    volume: Number(r.regularMarketVolume ?? 0),
    time: Number(r.regularMarketTime ?? 0),
    provider: "yahoo",
  };
}

// Cache in memory: { data, ts }
let _cache: { data: LiveQuote[]; ts: number } | null = null;
const CACHE_TTL_MS = 60_000; // 60 seconds

async function fetchFromYahoo(tickers: string[]): Promise<LiveQuote[]> {
  const tickerStr = tickers.join(",");
  const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(tickerStr)}&fields=${YF_FIELDS}&lang=en-US&region=IN`;

  const res = await fetch(url, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
      Accept: "application/json",
    },
    signal: AbortSignal.timeout(12_000),
  });

  if (!res.ok) throw new Error(`Yahoo Finance returned ${res.status}`);

  const json = await res.json() as {
    quoteResponse?: { result?: Record<string, unknown>[] };
  };
  const results = json?.quoteResponse?.result ?? [];

  // Build reverse map: yf_ticker → db_symbol
  const reverseMap = Object.fromEntries(
    Object.entries(NIFTY50_TICKERS).map(([sym, yf]) => [yf, sym])
  );

  return results.map((r) => {
    const yfSym = String(r.symbol ?? "");
    const dbSym = reverseMap[yfSym] ?? yfSym.replace(/\.NS$/, "");
    return mapResult(dbSym, r);
  });
}

// GET /api/quotes?symbols=RELIANCE,INFY,TCS  (optional — omit for all Nifty50)
export async function GET(req: NextRequest) {
  // Return from in-process cache if fresh
  if (_cache && Date.now() - _cache.ts < CACHE_TTL_MS) {
    const requested = req.nextUrl.searchParams.get("symbols");
    const data = requested
      ? _cache.data.filter((q) => requested.split(",").includes(q.symbol))
      : _cache.data;
    return NextResponse.json(data, {
      headers: { "X-Cache": "HIT", "Cache-Control": "public,max-age=60" },
    });
  }

  const requested = req.nextUrl.searchParams.get("symbols");
  const symbolList = requested ? requested.split(",") : Object.keys(NIFTY50_TICKERS);
  const tickers = symbolList
    .map((s) => NIFTY50_TICKERS[s] ?? `${s}.NS`)
    .filter(Boolean);

  try {
    const quotes = await fetchFromYahoo(tickers);
    // Update cache with all results
    if (!requested) {
      _cache = { data: quotes, ts: Date.now() };
    }
    return NextResponse.json(quotes, {
      headers: { "X-Cache": "MISS", "Cache-Control": "public,max-age=60" },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: "Failed to fetch live quotes", detail: msg },
      { status: 503 }
    );
  }
}
