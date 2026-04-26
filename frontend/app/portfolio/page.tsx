export const dynamic = "force-dynamic";

import { Navbar } from "@/components/Navbar";
import { createSupabaseServerClient } from "@/lib/supabase-server";
import { redirect } from "next/navigation";
import { SignalBadge } from "@/components/dashboard/SignalBadge";
import type { SignalLabel } from "@/types";

function formatINR(n: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n);
}

function pnlColor(n: number) {
  return n >= 0 ? "text-emerald-400" : "text-red-400";
}

export default async function PortfolioPage() {
  const supabase = await createSupabaseServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  const { data: holdings } = await supabase
    .from("holdings")
    .select(
      "id, symbol, quantity, avg_price, current_price, pnl, pnl_pct, value, provider"
    )
    .eq("user_id", user.id)
    .order("value", { ascending: false });

  const { data: signals } = await supabase
    .from("signals")
    .select("symbol, signal, composite_score, date")
    .in("symbol", (holdings ?? []).map((h) => h.symbol))
    .order("date", { ascending: false })
    .limit(200);

  const latestSignalBySymbol = new Map<string, { signal: string; composite_score: number }>();
  for (const s of signals ?? []) {
    if (!latestSignalBySymbol.has(s.symbol))
      latestSignalBySymbol.set(s.symbol, { signal: s.signal, composite_score: s.composite_score });
  }

  const rows = holdings ?? [];
  const totalInvested = rows.reduce(
    (sum, h) => sum + Number(h.avg_price) * Number(h.quantity),
    0
  );
  const currentValue = rows.reduce((sum, h) => sum + Number(h.value), 0);
  const totalPnl = currentValue - totalInvested;
  const totalPnlPct = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
          <p className="text-sm text-muted-foreground mt-1">Your holdings and performance</p>
        </div>

        {/* Summary bar */}
        {rows.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Invested", value: formatINR(totalInvested) },
              { label: "Current Value", value: formatINR(currentValue) },
              {
                label: "P&L",
                value: `${totalPnl >= 0 ? "+" : ""}${formatINR(totalPnl)}`,
                colored: true,
                n: totalPnl,
              },
              {
                label: "Return",
                value: `${totalPnlPct >= 0 ? "+" : ""}${totalPnlPct.toFixed(2)}%`,
                colored: true,
                n: totalPnlPct,
              },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl bg-card border border-border px-5 py-4"
              >
                <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground mb-1">
                  {item.label}
                </p>
                <p
                  className={`text-xl font-semibold ${
                    item.colored ? pnlColor(item.n ?? 0) : "text-foreground"
                  }`}
                >
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Holdings table */}
        <div className="rounded-2xl bg-card border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/30">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Symbol</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">
                  Qty
                </th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">
                  Avg Price
                </th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">
                  Current
                </th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">P&L</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">
                  Value
                </th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">
                  Signal
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((h, i) => {
                const sig = latestSignalBySymbol.get(h.symbol);
                const pnl = Number(h.pnl);
                const pnlPct = Number(h.pnl_pct);
                return (
                  <tr
                    key={h.id}
                    className={`border-b border-border last:border-0 hover:bg-secondary/30 transition-colors ${
                      i % 2 === 0 ? "" : "bg-secondary/10"
                    }`}
                  >
                    <td className="px-4 py-3 font-mono font-semibold text-foreground">
                      {h.symbol}
                    </td>
                    <td className="px-4 py-3 text-right text-muted-foreground hidden sm:table-cell">
                      {Number(h.quantity)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                      ₹{Number(h.avg_price).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-foreground">
                      ₹{Number(h.current_price).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      <span className={pnlColor(pnl)}>
                        {pnl >= 0 ? "+" : ""}
                        {formatINR(pnl)}
                      </span>
                      <span className={`ml-1 text-xs ${pnlColor(pnlPct)}`}>
                        ({pnlPct >= 0 ? "+" : ""}
                        {pnlPct.toFixed(2)}%)
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-foreground hidden md:table-cell">
                      {formatINR(Number(h.value))}
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      {sig ? (
                        <SignalBadge signal={sig.signal as SignalLabel} />
                      ) : (
                        <span className="text-muted-foreground text-xs">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-12 text-center text-sm text-muted-foreground"
                  >
                    No holdings yet. Add stocks to your portfolio to track performance.
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
