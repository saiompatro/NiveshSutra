export const dynamic = "force-dynamic";

import { Navbar } from "@/components/Navbar";
import { StatCard } from "@/components/dashboard/StatCard";
import { SignalsTable } from "@/components/dashboard/SignalsTable";
import { NiftySparkline } from "@/components/dashboard/NiftySparkline";
import { LiveNiftyQuote } from "@/components/dashboard/LiveNiftyQuote";
import { LiveNiftyStat } from "@/components/dashboard/LiveNiftyStat";
import { createSupabaseServerClient, createSupabaseAdminClient } from "@/lib/supabase-server";
import type { Signal, Alert } from "@/types";

type HoldingRow = {
  id: string;
  symbol: string;
  quantity: number;
  avg_buy_price: number;
};

type LiveStockRow = {
  symbol: string;
  current_price: number;
};

function formatINR(n: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
    }).format(n);
}

async function fetchLiveQuoteMap() {
  const base = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  if (!base) return new Map<string, LiveStockRow>();

  try {
    const res = await fetch(`${base.replace(/\/$/, "")}/api/v1/stocks/live`, {
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) return new Map<string, LiveStockRow>();
    const data = (await res.json()) as LiveStockRow[];
    return new Map(data.map((row) => [row.symbol, row]));
  } catch {
    return new Map<string, LiveStockRow>();
  }
}

export default async function DashboardPage() {
  const [supabase, admin] = await Promise.all([
    createSupabaseServerClient(),
    createSupabaseAdminClient(),
  ]);

  const { data: { user } } = await supabase.auth.getUser();

  // Parallel Supabase reads — no Render API cold-start
  const [signalsRes, ohlcvRes, alertsRes, holdingsRes, liveQuotesRes] = await Promise.allSettled([
    admin
      .from("signals")
      .select("symbol, date, signal, composite_score, technical_score, sentiment_score, momentum_score, confidence, explanation")
      .order("composite_score", { ascending: false })
      .limit(20),

    admin
      .from("ohlcv")
      .select("date, close")
      .eq("symbol", "^NSEI")
      .order("date", { ascending: false })
      .limit(90),

    user
      ? supabase
          .from("alerts")
          .select("id, alert_type, title, message, symbol, is_read, created_at")
          .eq("user_id", user.id)
          .eq("is_read", false)
          .order("created_at", { ascending: false })
          .limit(5)
      : Promise.resolve({ data: [], error: null }),

    user
      ? supabase
          .from("holdings")
          .select("id, symbol, quantity, avg_buy_price")
          .eq("user_id", user.id)
      : Promise.resolve({ data: [], error: null }),

    fetchLiveQuoteMap(),
  ]);

  const signals: Signal[] =
    signalsRes.status === "fulfilled" ? (signalsRes.value.data ?? []) : [];

  const niftyHistory: { date: string; close: number }[] =
    ohlcvRes.status === "fulfilled"
      ? [...(ohlcvRes.value.data ?? [])]
          .reverse()
          .map((r) => ({ date: r.date, close: Number(r.close) }))
      : [];

  const alerts: Alert[] =
    alertsRes.status === "fulfilled" ? (alertsRes.value.data ?? []) : [];

  const holdingRows =
    holdingsRes.status === "fulfilled" ? ((holdingsRes.value.data ?? []) as HoldingRow[]) : [];
  const liveQuoteMap =
    liveQuotesRes.status === "fulfilled" ? liveQuotesRes.value : new Map<string, LiveStockRow>();

  const holdings = holdingRows.map((holding) => {
    const avgPrice = Number(holding.avg_buy_price);
    const quantity = Number(holding.quantity);
    const currentPrice = Number(liveQuoteMap.get(holding.symbol)?.current_price ?? avgPrice);
    const value = quantity * currentPrice;

    return {
      ...holding,
      avg_price: avgPrice,
      current_price: currentPrice,
      value,
    };
  });

  const totalInvested = holdings.reduce(
    (sum: number, h: { avg_price: number; quantity: number }) => sum + h.avg_price * h.quantity,
    0
  );
  const currentValue = holdings.reduce(
    (sum: number, h: { value: number }) => sum + h.value,
    0
  );
  const pnl = currentValue - totalInvested;
  const pnlPct = totalInvested > 0 ? (pnl / totalInvested) * 100 : 0;
  const hasPortfolio = holdings.length > 0;

  return (
    <>
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* ── Top stat row ────────────────────────────────────── */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard
            label="Portfolio Value"
            value={hasPortfolio ? formatINR(currentValue) : "—"}
            trend={hasPortfolio ? pnlPct : undefined}
            sub={hasPortfolio ? `${formatINR(pnl)} P&L` : user ? "Add holdings to track" : "Sign in to track"}
          />
          <LiveNiftyStat
            fallbackValue={
              niftyHistory.length
                ? niftyHistory[niftyHistory.length - 1].close.toLocaleString("en-IN", {
                    maximumFractionDigits: 0,
                  })
                : "—"
            }
            fallbackSub="Last close · fetching live…"
          />
          <StatCard
            label="Unread Alerts"
            value={String(alerts.length)}
            sub={alerts.length ? alerts[0]?.title : "All clear"}
            className="sm:col-span-2 lg:col-span-1"
          />
        </section>

        {/* ── Nifty sparkline ─────────────────────────────────── */}
        {niftyHistory.length > 0 && (
          <section className="rounded-2xl bg-card border border-border p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                Nifty 50 — 90 days
              </p>
              {/* Live % change loads client-side without blocking the page */}
              <LiveNiftyQuote />
            </div>
            <NiftySparkline data={niftyHistory} />
          </section>
        )}

        {/* ── Signals ─────────────────────────────────────────── */}
        <section className="rounded-2xl bg-card border border-border p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground mb-1">
                Today&apos;s Signals
              </p>
              <p className="text-sm text-muted-foreground">
                Top 20 by composite score
              </p>
            </div>
            <p className="text-xs text-muted-foreground">{signals.length} signals</p>
          </div>
          <SignalsTable signals={signals} />
        </section>

        {/* ── Recent alerts ───────────────────────────────────── */}
        {alerts.length > 0 && (
          <section className="rounded-2xl bg-card border border-border p-6">
            <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground mb-4">
              Recent Alerts
            </p>
            <ul className="space-y-3">
              {alerts.map((a) => (
                <li key={a.id} className="flex items-start gap-3 text-sm">
                  <span
                    className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${
                      a.alert_type === "signal_change"
                        ? "bg-indigo-400"
                        : a.alert_type === "sentiment_shift"
                        ? "bg-yellow-400"
                        : "bg-orange-400"
                    }`}
                  />
                  <div>
                    <p className="font-medium text-foreground">{a.title}</p>
                    <p className="text-muted-foreground text-xs mt-0.5">{a.message}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </>
  );
}
