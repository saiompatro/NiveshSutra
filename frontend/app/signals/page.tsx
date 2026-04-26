export const dynamic = "force-dynamic";

import { Navbar } from "@/components/Navbar";
import { createSupabaseAdminClient } from "@/lib/supabase-server";
import { SignalBadge } from "@/components/dashboard/SignalBadge";
import type { SignalLabel } from "@/types";

const SIGNAL_ORDER: Record<SignalLabel, number> = {
  strong_buy: 0,
  buy: 1,
  hold: 2,
  sell: 3,
  strong_sell: 4,
};

export default async function SignalsPage() {
  const admin = await createSupabaseAdminClient();

  const { data: signals } = await admin
    .from("signals")
    .select(
      "symbol, date, signal, composite_score, technical_score, sentiment_score, momentum_score, confidence, explanation"
    )
    .order("date", { ascending: false })
    .order("composite_score", { ascending: false })
    .limit(500);

  // Keep only the most recent date's signals
  const mostRecentDate = signals?.[0]?.date ?? null;
  const todaySignals = signals?.filter((s) => s.date === mostRecentDate) ?? [];

  const sorted = [...todaySignals].sort(
    (a, b) =>
      (SIGNAL_ORDER[a.signal as SignalLabel] ?? 2) -
      (SIGNAL_ORDER[b.signal as SignalLabel] ?? 2)
  );

  const counts = sorted.reduce<Record<string, number>>((acc, s) => {
    acc[s.signal] = (acc[s.signal] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Signals</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {mostRecentDate ? `Latest signals — ${mostRecentDate}` : "No signals yet"}
            </p>
          </div>
          <p className="text-xs text-muted-foreground mt-1">{sorted.length} total</p>
        </div>

        {/* Summary pills */}
        {sorted.length > 0 && (
          <div className="flex flex-wrap gap-3">
            {(["strong_buy", "buy", "hold", "sell", "strong_sell"] as SignalLabel[]).map(
              (label) =>
                counts[label] ? (
                  <div
                    key={label}
                    className="flex items-center gap-2 rounded-xl bg-card border border-border px-4 py-2"
                  >
                    <SignalBadge signal={label} />
                    <span className="text-sm font-semibold text-foreground">
                      {counts[label]}
                    </span>
                  </div>
                ) : null
            )}
          </div>
        )}

        {/* Full table */}
        <div className="rounded-2xl bg-card border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/30">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Symbol</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Signal</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Score</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">
                  Confidence
                </th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">
                  Technical
                </th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">
                  Sentiment
                </th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden xl:table-cell">
                  Momentum
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((s, i) => (
                <tr
                  key={s.symbol}
                  className={`border-b border-border last:border-0 hover:bg-secondary/30 transition-colors ${
                    i % 2 === 0 ? "" : "bg-secondary/10"
                  }`}
                >
                  <td className="px-4 py-3 font-mono font-semibold text-foreground">
                    {s.symbol}
                  </td>
                  <td className="px-4 py-3">
                    <SignalBadge signal={s.signal as SignalLabel} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {(s.composite_score >= 0 ? "+" : "") + s.composite_score.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground hidden md:table-cell">
                    {(s.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-muted-foreground hidden lg:table-cell">
                    {(s.technical_score >= 0 ? "+" : "") + s.technical_score.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-muted-foreground hidden lg:table-cell">
                    {(s.sentiment_score >= 0 ? "+" : "") + s.sentiment_score.toFixed(3)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-muted-foreground hidden xl:table-cell">
                    {(s.momentum_score >= 0 ? "+" : "") + s.momentum_score.toFixed(3)}
                  </td>
                </tr>
              ))}
              {sorted.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-12 text-center text-sm text-muted-foreground"
                  >
                    No signals yet — run the pipeline to generate signals.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
