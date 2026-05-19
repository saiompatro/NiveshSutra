export const dynamic = "force-dynamic";

import { Navbar } from "@/components/Navbar";
import { LivePricesOverlay } from "@/components/stocks/LivePricesOverlay";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type OhlcvRow = { symbol: string; date: string; close: number; volume: number };
type SignalRow = { symbol: string; signal: string; composite_score: number; date: string };

async function fetchLatestOhlcv(): Promise<OhlcvRow[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stocks`, {
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) return [];
    return (await res.json()) as OhlcvRow[];
  } catch {
    return [];
  }
}

async function fetchSignals(): Promise<SignalRow[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/signals`, {
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) return [];
    return (await res.json()) as SignalRow[];
  } catch {
    return [];
  }
}

export default async function StocksPage() {
  const [stocks, signals] = await Promise.all([fetchLatestOhlcv(), fetchSignals()]);

  // Deduplicate: most recent row per symbol
  const latestBySymbol = new Map<string, OhlcvRow>();
  for (const row of stocks) {
    if (!latestBySymbol.has(row.symbol)) latestBySymbol.set(row.symbol, row);
  }

  const latestSignalBySymbol = new Map<string, { signal: string; composite_score: number }>();
  for (const s of signals) {
    if (!latestSignalBySymbol.has(s.symbol))
      latestSignalBySymbol.set(s.symbol, {
        signal: s.signal,
        composite_score: s.composite_score,
      });
  }

  const rows = Array.from(latestBySymbol.values())
    .filter((r) => r.symbol !== "^NSEI")
    .map((r) => {
      const sig = latestSignalBySymbol.get(r.symbol);
      return {
        symbol: r.symbol,
        date: r.date,
        close: Number(r.close),
        volume: Number(r.volume),
        signal: sig?.signal ?? null,
        composite_score: sig?.composite_score ?? null,
      };
    })
    .sort((a, b) => a.symbol.localeCompare(b.symbol));

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Stocks</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Nifty 50 - live NSE prices, signals from last pipeline run
          </p>
        </div>

        {/* LivePricesOverlay is a client component:
            renders the table server-side with last-close prices,
            then fetches live quotes from /api/quotes (Yahoo Finance) and updates prices */}
        <LivePricesOverlay rows={rows} />
      </main>
    </>
  );
}
