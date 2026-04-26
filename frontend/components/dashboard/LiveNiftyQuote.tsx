"use client";

import { useEffect, useState } from "react";

interface LiveQuote {
  symbol: string;
  price: number;
  change_pct: number;
}

export function LiveNiftyQuote() {
  const [quote, setQuote] = useState<LiveQuote | null>(null);
  const [tried, setTried] = useState(false);

  useEffect(() => {
    async function fetchQuote() {
      try {
        const res = await fetch("/api/quotes?symbols=^NSEI", {
          signal: AbortSignal.timeout(15_000),
        });
        if (!res.ok) throw new Error(`${res.status}`);
        const data: LiveQuote[] = await res.json();
        const nifty = data.find((q) => q.symbol === "^NSEI");
        if (nifty) setQuote(nifty);
      } catch {
        // silently ignore — sparkline already shows historical context
      } finally {
        setTried(true);
      }
    }
    fetchQuote();
  }, []);

  if (!tried) {
    return (
      <span className="text-xs text-muted-foreground animate-pulse">
        fetching live…
      </span>
    );
  }

  if (!quote) return null;

  const up = quote.change_pct >= 0;
  return (
    <span className={`text-sm font-semibold ${up ? "text-emerald-400" : "text-red-400"}`}>
      {up ? "▲" : "▼"} {Math.abs(quote.change_pct).toFixed(2)}%
    </span>
  );
}
