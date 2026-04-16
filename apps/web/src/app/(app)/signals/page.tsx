"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  fetchSignals as fetchSignalsApi,
  fetchSignalsSummary,
  fetchProfile,
} from "@/lib/api";
import type { Profile } from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
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
import { Zap, TrendingUp, TrendingDown, Minus, Shield, Info } from "lucide-react";

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

// Personalization: adjust how signals are displayed based on risk profile
function personalizeSignals(
  signals: Signal[],
  riskProfile: string
): Signal[] {
  const sorted = [...signals];

  switch (riskProfile) {
    case "conservative":
      // Conservative users: prioritize high-confidence signals, move aggressive calls down
      return sorted.sort((a, b) => {
        // Prefer hold/buy with high confidence
        const aScore = getConservativeScore(a);
        const bScore = getConservativeScore(b);
        return bScore - aScore;
      });
    case "aggressive":
      // Aggressive users: prioritize strong signals (both buy and sell)
      return sorted.sort((a, b) => {
        const aScore = getAggressiveScore(a);
        const bScore = getAggressiveScore(b);
        return bScore - aScore;
      });
    default:
      return sorted;
  }
}

function getConservativeScore(s: Signal): number {
  const signalWeights: Record<string, number> = {
    buy: 3,
    hold: 2,
    strong_buy: 1, // De-emphasize overly aggressive
    sell: 0,
    strong_sell: -1,
  };
  return (signalWeights[s.signal] ?? 0) + s.confidence * 2;
}

function getAggressiveScore(s: Signal): number {
  // Aggressive users want strong signals in either direction
  const signalWeights: Record<string, number> = {
    strong_buy: 4,
    strong_sell: 3,
    buy: 2,
    sell: 1,
    hold: 0,
  };
  return (signalWeights[s.signal] ?? 0) + s.confidence * 2;
}

function getConfidenceThreshold(riskProfile: string): number {
  switch (riskProfile) {
    case "conservative":
      return 0.5; // Only show signals with > 50% confidence
    case "aggressive":
      return 0.2; // Show almost all signals
    default:
      return 0.3;
  }
}

function getPositionSizeHint(riskProfile: string, signal: string): string {
  const isActionable = ["strong_buy", "buy", "sell", "strong_sell"].includes(signal);
  if (!isActionable) return "";

  switch (riskProfile) {
    case "conservative":
      return signal === "buy" ? "2-3% of portfolio" : signal === "strong_buy" ? "3-5% of portfolio" : "";
    case "aggressive":
      return signal === "strong_buy" ? "8-12% of portfolio" : signal === "buy" ? "5-8% of portfolio" : "";
    default:
      return signal === "strong_buy" ? "5-8% of portfolio" : signal === "buy" ? "3-5% of portfolio" : "";
  }
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [summary, setSummary] = useState<SignalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [profile, setProfile] = useState<Profile | null>(null);
  const router = useRouter();

  useEffect(() => {
    async function loadSignals() {
      try {
        const [signalsRes, summaryRes, profileRes] = await Promise.allSettled([
          fetchSignalsApi(),
          fetchSignalsSummary(),
          fetchProfile(),
        ]);
        if (signalsRes.status === "fulfilled") setSignals(signalsRes.value);
        if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
        if (profileRes.status === "fulfilled") setProfile(profileRes.value);
      } catch {
        toast.error("Failed to load signals");
      } finally {
        setLoading(false);
      }
    }
    loadSignals();
  }, []);

  const riskProfile = profile?.risk_profile || "moderate";
  const confidenceThreshold = getConfidenceThreshold(riskProfile);

  const filtered = useMemo(() => {
    let result = signals;

    // Apply signal type filter
    if (filter !== "all") {
      result = result.filter((s) => s.signal === filter);
    }

    // Apply personalization
    result = personalizeSignals(result, riskProfile);

    return result;
  }, [signals, filter, riskProfile]);

  // Separate into recommended (above threshold) and other signals
  const { recommended, other } = useMemo(() => {
    const rec: Signal[] = [];
    const oth: Signal[] = [];
    for (const s of filtered) {
      if (s.confidence >= confidenceThreshold && s.signal !== "hold") {
        rec.push(s);
      } else {
        oth.push(s);
      }
    }
    return { recommended: rec, other: oth };
  }, [filtered, confidenceThreshold]);

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
          AI-generated trading signals personalized for your risk profile
        </p>
      </div>

      {/* Risk Profile Banner */}
      {profile?.risk_profile && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex items-center gap-3 py-3">
            <Shield className="h-5 w-5 text-primary" />
            <div className="flex-1">
              <p className="text-sm font-medium">
                Signals personalized for your{" "}
                <span className="capitalize font-bold">{profile.risk_profile}</span>{" "}
                risk profile
              </p>
              <p className="text-xs text-muted-foreground">
                {riskProfile === "conservative" &&
                  "Showing higher-confidence signals. Aggressive calls are de-prioritized."}
                {riskProfile === "moderate" &&
                  "Balanced signal view with standard confidence thresholds."}
                {riskProfile === "aggressive" &&
                  "All signals shown. Strong directional signals are prioritized."}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

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
            <div>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                {recommended.length > 0
                  ? `Recommended Signals (${recommended.length})`
                  : "All Signals"}
              </CardTitle>
              {recommended.length > 0 && (
                <CardDescription className="mt-1">
                  Signals above {Math.round(confidenceThreshold * 100)}%
                  confidence threshold for your profile
                </CardDescription>
              )}
            </div>
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
                <TableHead className="hidden lg:table-cell text-right">
                  Suggested Size
                </TableHead>
                <TableHead className="hidden sm:table-cell text-right">
                  Date
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Recommended signals first */}
              {recommended.map((s, i) => (
                <SignalRow
                  key={`rec-${s.symbol}-${i}`}
                  signal={s}
                  riskProfile={riskProfile}
                  onClick={() => router.push(`/stocks/${s.symbol}`)}
                />
              ))}
              {/* Separator if both groups have items */}
              {recommended.length > 0 && other.length > 0 && (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="bg-muted/30 py-2 text-center text-xs text-muted-foreground"
                  >
                    <Info className="mr-1 inline h-3 w-3" />
                    Other signals (below confidence threshold)
                  </TableCell>
                </TableRow>
              )}
              {/* Other signals */}
              {other.map((s, i) => (
                <SignalRow
                  key={`oth-${s.symbol}-${i}`}
                  signal={s}
                  riskProfile={riskProfile}
                  dimmed={recommended.length > 0}
                  onClick={() => router.push(`/stocks/${s.symbol}`)}
                />
              ))}
              {recommended.length === 0 && other.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center text-muted-foreground"
                  >
                    No signals found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function SignalRow({
  signal: s,
  riskProfile,
  dimmed,
  onClick,
}: {
  signal: Signal;
  riskProfile: string;
  dimmed?: boolean;
  onClick: () => void;
}) {
  const sizeHint = getPositionSizeHint(riskProfile, s.signal);

  return (
    <TableRow
      className={`cursor-pointer ${dimmed ? "opacity-60" : ""}`}
      onClick={onClick}
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
      <TableCell className="hidden lg:table-cell text-right text-xs text-muted-foreground">
        {sizeHint || "-"}
      </TableCell>
      <TableCell className="hidden sm:table-cell text-right text-muted-foreground">
        {new Date(s.created_at).toLocaleDateString("en-IN")}
      </TableCell>
    </TableRow>
  );
}
