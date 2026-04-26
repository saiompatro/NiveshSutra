export const dynamic = "force-dynamic";

import { Navbar } from "@/components/Navbar";
import { createSupabaseAdminClient } from "@/lib/supabase-server";
import { LivePricesOverlay } from "@/components/stocks/LivePricesOverlay";

export default async function StocksPage() {
  const admin = await createSupabaseAdminClient();

  // Latest OHLCV per symbol (order desc → first row per symbol = latest)
  const { data: ohlcv } = await admin
    .from("ohlcv")
    .select("symbol, date, close, volume")
    .order("date", { ascending: false })
    .limit(500);

  // Deduplicate: most recent row per symbol
  type OhlcvRow = { symbol: string; date: string; close: number; volume: number };
  const latestBySymbol = new Map<string, OhlcvRow>();
  for (const row of ohlcv ?? []) {
    if (!latestBySymbol.has(row.symbol)) latestBySymbol.set(row.symbol, row as OhlcvRow);
  }

  const { data: signals } = await admin
    .from("signals")
    .select("symbol, signal, composite_score, date")
    .order("date", { ascending: false })
    .limit(200);

  const latestSignalBySymbol = new Map<string, { signal: string; composite_score: number }>();
  for (const s of signals ?? []) {
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
            renders the table server-side with last-close prices from Supabase,
            then fetches live quotes from /api/quotes (Yahoo Finance) and updates prices */}
        <LivePricesOverlay rows={rows} />
      </main>
    </>
  );
}
