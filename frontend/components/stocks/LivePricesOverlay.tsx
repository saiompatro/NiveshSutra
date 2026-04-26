"use client";

import { useEffect, useState } from "react";
import { SignalBadge } from "@/components/dashboard/SignalBadge";
import type { SignalLabel } from "@/types";

interface BaseRow {
  symbol: string;
  close: number;      // last Supabase close
  volume: number;
  date: string;
  signal: string | null;
  composite_score: number | null;
}

interface LiveQuote {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  provider: string;
}

function pctColor(n: number) {
  return n > 0 ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-muted-foreground";
}

export function LivePricesOverlay({ rows }: { rows: BaseRow[] }) {
  const [liveMap, setLiveMap] = useState<Record<string, LiveQuote>>({});
  const [status, setStatus] = useState<"loading" | "live" | "offline">("loading");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/quotes", {
          signal: AbortSignal.timeout(15_000),
        });
        if (!res.ok) throw new Error(`${res.status}`);
        const data: LiveQuote[] = await res.json();
        const map: Record<string, LiveQuote> = {};
        for (const q of data) map[q.symbol] = q;
        setLiveMap(map);
        setStatus("live");
      } catch {
        setStatus("offline");
      }
    }
    load();
  }, []);

  return (
    <div className="rounded-2xl bg-card border border-border overflow-hidden">
      {/* Status bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-secondary/20">
        <p className="text-xs text-muted-foreground">
          {rows.length} stocks
        </p>
        <span
          className={`text-xs font-medium flex items-center gap-1.5 ${
            status === "live"
              ? "text-emerald-400"
              : status === "loading"
              ? "text-muted-foreground animate-pulse"
              : "text-yellow-400"
          }`}
        >
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full ${
              status === "live"
                ? "bg-emerald-400"
                : status === "loading"
                ? "bg-zinc-500"
                : "bg-yellow-400"
            }`}
          />
          {status === "live"
            ? "Live · Yahoo Finance"
            : status === "loading"
            ? "Fetching live prices…"
            : "Last close · live unavailable"}
        </span>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-secondary/30">
            <th className="text-left px-4 py-3 font-medium text-muted-foreground">Symbol</th>
            <th className="text-right px-4 py-3 font-medium text-muted-foreground">Price</th>
            <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">
              Change
            </th>
            <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">
              Volume
            </th>
            <th className="text-left px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">
              Signal
            </th>
            <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">
              Score
            </th>
            <th className="text-right px-4 py-3 font-medium text-muted-foreground">Date</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const live = liveMap[r.symbol];
            const price = live?.price ?? r.close;
            const changePct = live?.change_pct ?? null;
            const volume = live?.volume ?? r.volume;

            return (
              <tr
                key={r.symbol}
                className={`border-b border-border last:border-0 hover:bg-secondary/30 transition-colors ${
                  i % 2 === 0 ? "" : "bg-secondary/10"
                }`}
              >
                <td className="px-4 py-3 font-mono font-semibold text-foreground">
                  {r.symbol}
                </td>
                <td className="px-4 py-3 text-right font-mono text-foreground">
                  ₹{price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3 text-right hidden sm:table-cell">
                  {changePct != null ? (
                    <span className={`font-mono text-sm font-medium ${pctColor(changePct)}`}>
                      {changePct >= 0 ? "▲" : "▼"} {Math.abs(changePct).toFixed(2)}%
                    </span>
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-muted-foreground hidden md:table-cell">
                  {volume > 0 ? `${(volume / 1_000_000).toFixed(2)}M` : "—"}
                </td>
                <td className="px-4 py-3 hidden sm:table-cell">
                  {r.signal ? (
                    <SignalBadge signal={r.signal as SignalLabel} />
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right font-mono text-muted-foreground hidden lg:table-cell">
                  {r.composite_score != null
                    ? (r.composite_score >= 0 ? "+" : "") + r.composite_score.toFixed(3)
                    : "—"}
                </td>
                <td className="px-4 py-3 text-right text-muted-foreground text-xs">{r.date}</td>
              </tr>
            );
          })}
          {rows.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-12 text-center text-sm text-muted-foreground">
                No data yet — run the pipeline to ingest OHLCV data.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
