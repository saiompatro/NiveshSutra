"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Zap, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface Signal {
  symbol: string;
  signal: string;
  confidence: number;
  technical_score: number;
  sentiment_score: number;
  momentum_score: number;
  created_at: string;
}

interface SignalSummary {
  strong_buy: number;
  buy: number;
  hold: number;
  sell: number;
  strong_sell: number;
  total: number;
}

const SIGNAL_TYPES = ["all", "strong_buy", "buy", "hold", "sell", "strong_sell"];

function signalColor(signal: string): string {
  switch (signal) {
    case "strong_buy":
      return "bg-green-500/20 text-green-400 border-green-500/30";
    case "buy":
      return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    case "hold":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "sell":
      return "bg-orange-500/20 text-orange-400 border-orange-500/30";
    case "strong_sell":
      return "bg-red-500/20 text-red-400 border-red-500/30";
    default:
      return "";
  }
}

function formatSignal(signal: string): string {
  return signal.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function SignalIcon({ signal }: { signal: string }) {
  if (signal === "strong_buy" || signal === "buy")
    return <TrendingUp className="h-4 w-4 text-green-400" />;
  if (signal === "strong_sell" || signal === "sell")
    return <TrendingDown className="h-4 w-4 text-red-400" />;
  return <Minus className="h-4 w-4 text-yellow-400" />;
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [summary, setSummary] = useState<SignalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const router = useRouter();

  useEffect(() => {
    async function fetchSignals() {
      try {
        const [signalsRes, summaryRes] = await Promise.allSettled([
          apiFetch<Signal[]>("/signals"),
          apiFetch<SignalSummary>("/signals/summary"),
        ]);
        if (signalsRes.status === "fulfilled") setSignals(signalsRes.value);
        if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
      } catch {
        toast.error("Failed to load signals");
      } finally {
        setLoading(false);
      }
    }
    fetchSignals();
  }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return signals;
    return signals.filter((s) => s.signal === filter);
  }, [signals, filter]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-5">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Signals</h1>
        <p className="text-sm text-muted-foreground">
          AI-generated trading signals for Nifty 50 stocks
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-3 grid-cols-2 sm:grid-cols-5">
          <Card
            className="cursor-pointer transition-colors hover:bg-muted/50"
            onClick={() => setFilter("strong_buy")}
          >
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Strong Buy</p>
              <p className="text-2xl font-bold text-green-400">
                {summary.strong_buy}
              </p>
            </CardContent>
          </Card>
          <Card
            className="cursor-pointer transition-colors hover:bg-muted/50"
            onClick={() => setFilter("buy")}
          >
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Buy</p>
              <p className="text-2xl font-bold text-emerald-400">
                {summary.buy}
              </p>
            </CardContent>
          </Card>
          <Card
            className="cursor-pointer transition-colors hover:bg-muted/50"
            onClick={() => setFilter("hold")}
          >
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Hold</p>
              <p className="text-2xl font-bold text-yellow-400">
                {summary.hold}
              </p>
            </CardContent>
          </Card>
          <Card
            className="cursor-pointer transition-colors hover:bg-muted/50"
            onClick={() => setFilter("sell")}
          >
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Sell</p>
              <p className="text-2xl font-bold text-orange-400">
                {summary.sell}
              </p>
            </CardContent>
          </Card>
          <Card
            className="cursor-pointer transition-colors hover:bg-muted/50"
            onClick={() => setFilter("strong_sell")}
          >
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Strong Sell</p>
              <p className="text-2xl font-bold text-red-400">
                {summary.strong_sell}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Signals Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              All Signals
            </CardTitle>
            <Select value={filter} onValueChange={(v) => setFilter(v ?? "all")}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by signal" />
              </SelectTrigger>
              <SelectContent>
                {SIGNAL_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type === "all" ? "All Signals" : formatSignal(type)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Signal</TableHead>
                <TableHead className="text-right">Confidence</TableHead>
                <TableHead className="hidden md:table-cell text-right">
                  Technical
                </TableHead>
                <TableHead className="hidden md:table-cell text-right">
                  Sentiment
                </TableHead>
                <TableHead className="hidden md:table-cell text-right">
                  Momentum
                </TableHead>
                <TableHead className="hidden sm:table-cell text-right">
                  Date
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="text-center text-muted-foreground"
                  >
                    No signals found
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((s, i) => (
                  <TableRow
                    key={`${s.symbol}-${i}`}
                    className="cursor-pointer"
                    onClick={() => router.push(`/stocks/${s.symbol}`)}
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <SignalIcon signal={s.signal} />
                        {s.symbol}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={signalColor(s.signal)}>
                        {formatSignal(s.signal)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="hidden sm:block h-2 w-16 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full bg-primary transition-all"
                            style={{ width: `${s.confidence * 100}%` }}
                          />
                        </div>
                        <span className="tabular-nums">
                          {(s.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-right tabular-nums">
                      {(s.technical_score * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-right tabular-nums">
                      {(s.sentiment_score * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-right tabular-nums">
                      {(s.momentum_score * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-right text-muted-foreground">
                      {new Date(s.created_at).toLocaleDateString("en-IN")}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
