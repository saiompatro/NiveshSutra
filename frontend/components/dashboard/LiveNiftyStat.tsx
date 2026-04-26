"use client";

import { useEffect, useState } from "react";
import { StatCard } from "./StatCard";

interface LiveQuote {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
}

interface Props {
  fallbackValue: string;
  fallbackSub: string;
}

export function LiveNiftyStat({ fallbackValue, fallbackSub }: Props) {
  const [quote, setQuote] = useState<LiveQuote | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetch_() {
      try {
        const res = await fetch("/api/quotes?symbols=^NSEI", {
          signal: AbortSignal.timeout(15_000),
        });
        if (!res.ok) throw new Error(`${res.status}`);
        const data: LiveQuote[] = await res.json();
        const nifty = data.find((q) => q.symbol === "^NSEI");
        if (nifty) setQuote(nifty);
      } catch {
        // fall back to Supabase values passed as props
      } finally {
        setLoading(false);
      }
    }
    fetch_();
  }, []);

  const value = quote
    ? quote.price.toLocaleString("en-IN", { maximumFractionDigits: 0 })
    : fallbackValue;
  const change = quote?.change ?? null;
  const changePct = quote?.change_pct ?? null;
  const sub = change != null
    ? `${change >= 0 ? "+" : ""}${change.toFixed(0)} pts · live`
    : fallbackSub;

  return (
    <StatCard
      label="Nifty 50"
      value={value}
      trend={changePct ?? undefined}
      sub={sub}
      loading={loading}
    />
  );
}
