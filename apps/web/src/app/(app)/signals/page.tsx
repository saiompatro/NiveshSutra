"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  fetchSignals as fetchSignalsApi,
  fetchSignalsSummary,
  fetchProfile,
  acceptSignal as acceptSignalApi,
  fetchAcceptedSignals,
  cancelAcceptedSignal,
  addHolding,
} from "@/lib/api";
import type { Profile, AcceptedSignal } from "@/lib/api";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Zap,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  Info,
  Check,
  X,
  Loader2,
} from "lucide-react";

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
  const [acceptedSignals, setAcceptedSignals] = useState<AcceptedSignal[]>([]);
  const [acceptDialog, setAcceptDialog] = useState<{
    open: boolean;
    signal: Signal | null;
  }>({ open: false, signal: null });
  const [acceptQty, setAcceptQty] = useState("");
  const [acceptPrice, setAcceptPrice] = useState("");
  const [accepting, setAccepting] = useState(false);
  const router = useRouter();

  useEffect(() => {
    async function loadSignals() {
      try {
        const [signalsRes, summaryRes, profileRes, acceptedRes] =
          await Promise.allSettled([
            fetchSignalsApi(),
            fetchSignalsSummary(),
            fetchProfile(),
            fetchAcceptedSignals(),
          ]);
        if (signalsRes.status === "fulfilled") setSignals(signalsRes.value);
        if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
        if (profileRes.status === "fulfilled") setProfile(profileRes.value);
        if (acceptedRes.status === "fulfilled")
          setAcceptedSignals(acceptedRes.value);
      } catch {
        toast.error("Failed to load signals");
      } finally {
        setLoading(false);
      }
    }
    loadSignals();
  }, []);

  async function handleAcceptSignal(e: React.FormEvent) {
    e.preventDefault();
    if (!acceptDialog.signal) return;
    setAccepting(true);
    const s = acceptDialog.signal;
    try {
      // Accept the signal
      await acceptSignalApi({
        symbol: s.symbol,
        signal_type: s.signal,
        signal_date: s.created_at,
        composite_score: s.confidence,
      });

      // For buy/strong_buy signals, also add to holdings if qty provided
      if (
        (s.signal === "buy" || s.signal === "strong_buy") &&
        acceptQty &&
        acceptPrice
      ) {
        await addHolding({
          symbol: s.symbol,
          quantity: Number(acceptQty),
          avg_buy_price: Number(acceptPrice),
        });
        toast.success(
          `Signal accepted and ${s.symbol} added to holdings`
        );
      } else {
        toast.success(`Signal for ${s.symbol} accepted`);
      }

      // Refresh accepted signals
      const updated = await fetchAcceptedSignals();
      setAcceptedSignals(updated);

      setAcceptDialog({ open: false, signal: null });
      setAcceptQty("");
      setAcceptPrice("");
    } catch (err: unknown) {
      toast.error(
        err instanceof Error ? err.message : "Failed to accept signal"
      );
    } finally {
      setAccepting(false);
    }
  }

  async function handleCancelAccepted(id: string, symbol: string) {
    try {
      await cancelAcceptedSignal(id);
      setAcceptedSignals((prev) => prev.filter((a) => a.id !== id));
      toast.success(`Stopped tracking ${symbol}`);
    } catch {
      toast.error("Failed to cancel signal");
    }
  }

  const acceptedSymbols = new Set(acceptedSignals.map((a) => a.symbol));

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
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Recommended signals first */}
              {recommended.map((s, i) => (
                <SignalRow
                  key={`rec-${s.symbol}-${i}`}
                  signal={s}
                  riskProfile={riskProfile}
                  isAccepted={acceptedSymbols.has(s.symbol)}
                  onAccept={() => setAcceptDialog({ open: true, signal: s })}
                  onClick={() => router.push(`/stocks/${s.symbol}`)}
                />
              ))}
              {/* Separator if both groups have items */}
              {recommended.length > 0 && other.length > 0 && (
                <TableRow>
                  <TableCell
                    colSpan={9}
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
                  isAccepted={acceptedSymbols.has(s.symbol)}
                  onAccept={() => setAcceptDialog({ open: true, signal: s })}
                  onClick={() => router.push(`/stocks/${s.symbol}`)}
                />
              ))}
              {recommended.length === 0 && other.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={9}
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

      {/* Accepted / Tracked Signals */}
      {acceptedSignals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Check className="h-4 w-4 text-green-400" />
              Tracked Signals
            </CardTitle>
            <CardDescription>
              You&apos;ll receive email alerts when these signals change
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Signal</TableHead>
                  <TableHead className="hidden sm:table-cell">
                    Confidence
                  </TableHead>
                  <TableHead className="hidden sm:table-cell">
                    Accepted
                  </TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {acceptedSignals.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <SignalIcon signal={a.signal_type} />
                        {a.symbol}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={signalColor(a.signal_type)}>
                        {formatSignal(a.signal_type)}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell tabular-nums">
                      {a.composite_score
                        ? `${(a.composite_score * 100).toFixed(0)}%`
                        : "-"}
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-muted-foreground">
                      {new Date(a.accepted_at).toLocaleDateString("en-IN")}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 text-xs text-destructive hover:text-destructive"
                        onClick={() => handleCancelAccepted(a.id, a.symbol)}
                      >
                        <X className="mr-1 h-3 w-3" />
                        Stop
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Accept Signal Dialog */}
      <Dialog
        open={acceptDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setAcceptDialog({ open: false, signal: null });
            setAcceptQty("");
            setAcceptPrice("");
          }
        }}
      >
        <DialogContent>
          <form onSubmit={handleAcceptSignal}>
            <DialogHeader>
              <DialogTitle>
                Accept {acceptDialog.signal?.signal === "buy" || acceptDialog.signal?.signal === "strong_buy" ? "Buy" : acceptDialog.signal?.signal === "sell" || acceptDialog.signal?.signal === "strong_sell" ? "Sell" : "Hold"} Signal
              </DialogTitle>
              <DialogDescription>
                {acceptDialog.signal?.symbol} &mdash;{" "}
                {acceptDialog.signal
                  ? formatSignal(acceptDialog.signal.signal)
                  : ""}{" "}
                ({acceptDialog.signal
                  ? `${(acceptDialog.signal.confidence * 100).toFixed(0)}% confidence`
                  : ""})
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <p className="text-sm text-muted-foreground">
                Accepting this signal will track it for email notifications when the signal changes.
              </p>
              {(acceptDialog.signal?.signal === "buy" ||
                acceptDialog.signal?.signal === "strong_buy") && (
                <>
                  <p className="text-sm font-medium">
                    Optionally add to your portfolio:
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label htmlFor="accept-qty">Quantity</Label>
                      <Input
                        id="accept-qty"
                        type="number"
                        min="0"
                        step="1"
                        placeholder="0"
                        value={acceptQty}
                        onChange={(e) => setAcceptQty(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="accept-price">Buy Price (₹)</Label>
                      <Input
                        id="accept-price"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={acceptPrice}
                        onChange={(e) => setAcceptPrice(e.target.value)}
                      />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Leave blank to track without adding to holdings.
                  </p>
                </>
              )}
            </div>
            <DialogFooter>
              <DialogClose>
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </DialogClose>
              <Button type="submit" disabled={accepting}>
                {accepting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Accept Signal
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function SignalRow({
  signal: s,
  riskProfile,
  dimmed,
  isAccepted,
  onAccept,
  onClick,
}: {
  signal: Signal;
  riskProfile: string;
  dimmed?: boolean;
  isAccepted?: boolean;
  onAccept: () => void;
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
      <TableCell className="text-right">
        {isAccepted ? (
          <Badge variant="outline" className="gap-1 text-green-400 border-green-500/30">
            <Check className="h-3 w-3" />
            Tracked
          </Badge>
        ) : (
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onAccept();
            }}
          >
            Accept
          </Button>
        )}
      </TableCell>
    </TableRow>
  );
}
