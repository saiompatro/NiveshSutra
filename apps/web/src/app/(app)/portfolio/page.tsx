"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchHoldings as fetchHoldingsApi,
  fetchPortfolioPerformance,
  addHolding as addHoldingApi,
  deleteHolding as deleteHoldingApi,
  runOptimization as runOptimizationApi,
} from "@/lib/api";
import type { OptimizationResult } from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Plus, TrendingUp, TrendingDown, Sparkles, Loader2 } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import type { PieLabelRenderProps } from "recharts";

interface Holding {
  id: string;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  value: number;
}

interface PortfolioPerformance {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_pct: number;
  history?: Array<{ date: string; value: number; benchmark: number }>;
}

// Using OptimizationResult from api.ts import

const CHART_COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#f97316",
  "#14b8a6",
  "#6366f1",
];

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [performance, setPerformance] = useState<PortfolioPerformance | null>(null);
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Add holding form
  const [newSymbol, setNewSymbol] = useState("");
  const [newQty, setNewQty] = useState("");
  const [newAvgPrice, setNewAvgPrice] = useState("");
  const [addingHolding, setAddingHolding] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [holdingsRes, perfRes] = await Promise.allSettled([
        fetchHoldingsApi(),
        fetchPortfolioPerformance(),
      ]);
      if (holdingsRes.status === "fulfilled") setHoldings(holdingsRes.value);
      if (perfRes.status === "fulfilled") setPerformance(perfRes.value);
    } catch {
      toast.error("Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleAddHolding(e: React.FormEvent) {
    e.preventDefault();
    if (!newSymbol || !newQty || !newAvgPrice) return;
    setAddingHolding(true);
    try {
      await addHoldingApi({
        symbol: newSymbol.toUpperCase(),
        quantity: Number(newQty),
        avg_buy_price: Number(newAvgPrice),
      });
      toast.success(`${newSymbol.toUpperCase()} added to holdings`);
      setNewSymbol("");
      setNewQty("");
      setNewAvgPrice("");
      setDialogOpen(false);
      fetchData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to add holding");
    } finally {
      setAddingHolding(false);
    }
  }

  async function handleDeleteHolding(id: string, symbol: string) {
    try {
      await deleteHoldingApi(id);
      toast.success(`${symbol} removed from holdings`);
      fetchData();
    } catch {
      toast.error("Failed to remove holding");
    }
  }

  async function handleRunOptimization() {
    setOptimizing(true);
    try {
      const result = await runOptimizationApi();
      if (result) {
        setOptimization(result);
        toast.success("Portfolio optimization complete!");
      } else {
        toast.error("Optimization failed — ensure you have holdings and market data.");
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Optimization failed");
    } finally {
      setOptimizing(false);
    }
  }

  // Prepare pie chart data
  const allocationData = holdings.map((h) => ({
    name: h.symbol,
    value: h.value,
  }));

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <p className="text-sm text-muted-foreground">
            Manage your holdings and optimize allocation
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger
              render={
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Holding
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Holding</DialogTitle>
                <DialogDescription>
                  Enter the stock details to add to your portfolio.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddHolding} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="symbol">Symbol</Label>
                  <Input
                    id="symbol"
                    placeholder="e.g. RELIANCE"
                    value={newSymbol}
                    onChange={(e) => setNewSymbol(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="qty">Quantity</Label>
                  <Input
                    id="qty"
                    type="number"
                    min="1"
                    placeholder="Number of shares"
                    value={newQty}
                    onChange={(e) => setNewQty(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="avgPrice">Average Price (INR)</Label>
                  <Input
                    id="avgPrice"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Purchase price per share"
                    value={newAvgPrice}
                    onChange={(e) => setNewAvgPrice(e.target.value)}
                    required
                  />
                </div>
                <DialogFooter>
                  <DialogClose render={<Button variant="outline">Cancel</Button>} />
                  <Button type="submit" disabled={addingHolding}>
                    {addingHolding ? "Adding..." : "Add"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
          <Button
            variant="outline"
            onClick={handleRunOptimization}
            disabled={optimizing || holdings.length === 0}
          >
            {optimizing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            Optimize
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {performance && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Total Value</p>
              <p className="text-2xl font-bold">
                {formatCurrency(performance.total_value)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Total Invested</p>
              <p className="text-2xl font-bold">
                {formatCurrency(performance.total_invested)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Total P&L</p>
              <p
                className={`flex items-center gap-2 text-2xl font-bold ${
                  performance.total_pnl >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {performance.total_pnl >= 0 ? (
                  <TrendingUp className="h-5 w-5" />
                ) : (
                  <TrendingDown className="h-5 w-5" />
                )}
                {formatCurrency(performance.total_pnl)} (
                {performance.total_pnl_pct >= 0 ? "+" : ""}
                {performance.total_pnl_pct.toFixed(2)}%)
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Holdings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          {holdings.length === 0 ? (
            <p className="py-8 text-center text-muted-foreground">
              No holdings yet. Add your first stock above.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Avg Price</TableHead>
                  <TableHead className="text-right">Current</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                  <TableHead className="text-right">P&L %</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {holdings.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell className="font-medium">{h.symbol}</TableCell>
                    <TableCell className="text-right">{h.quantity}</TableCell>
                    <TableCell className="text-right">
                      {h.avg_price.toLocaleString("en-IN", {
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      {h.current_price.toLocaleString("en-IN", {
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell
                      className={`text-right ${
                        h.pnl >= 0 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {h.pnl >= 0 ? "+" : ""}
                      {formatCurrency(h.pnl)}
                    </TableCell>
                    <TableCell
                      className={`text-right ${
                        h.pnl_pct >= 0 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {h.pnl_pct >= 0 ? "+" : ""}
                      {h.pnl_pct.toFixed(2)}%
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(h.value)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => handleDeleteHolding(h.id, h.symbol)}
                      >
                        Remove
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Charts Row */}
      {holdings.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Allocation Pie */}
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Allocation</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={allocationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={(props: PieLabelRenderProps) =>
                      `${props.name ?? ""} ${(((props.percent as number) ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {allocationData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatCurrency(Number(value))}
                    contentStyle={{
                      backgroundColor: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      color: "hsl(var(--popover-foreground))",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Performance vs Nifty */}
          <Card>
            <CardHeader>
              <CardTitle>Performance vs Nifty 50</CardTitle>
            </CardHeader>
            <CardContent>
              {performance?.history && performance.history.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performance.history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="date"
                      stroke="#9ca3af"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(v) =>
                        new Date(v).toLocaleDateString("en-IN", {
                          month: "short",
                          day: "numeric",
                        })
                      }
                    />
                    <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--popover))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--popover-foreground))",
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#3b82f6"
                      name="Portfolio"
                      dot={false}
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="benchmark"
                      stroke="#6b7280"
                      name="Nifty 50"
                      dot={false}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="flex h-[300px] items-center justify-center text-muted-foreground">
                  Performance history unavailable
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Optimization Results */}
      {optimization && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Optimization Results</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Expected Annual Return</p>
                <p className="text-2xl font-bold text-green-400">
                  {((optimization.expected_return ?? 0) * 100).toFixed(1)}%
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Annual Volatility</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {((optimization.expected_risk ?? 0) * 100).toFixed(1)}%
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Recommended Allocation Pie */}
            <Card>
              <CardHeader>
                <CardTitle>Recommended Allocation</CardTitle>
                <CardDescription>
                  Sharpe Ratio: {(optimization.sharpe_ratio ?? 0).toFixed(2)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={optimization.allocations
                        .filter((a) => a.recommended_weight > 0.01)
                        .map((a) => ({
                          name: a.symbol,
                          value: a.recommended_weight,
                        }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                      label={(props: PieLabelRenderProps) =>
                        `${props.name ?? ""} ${(((props.value as number) ?? 0) * 100).toFixed(0)}%`
                      }
                    >
                      {optimization.allocations
                        .filter((a) => a.recommended_weight > 0.01)
                        .map((_, index) => (
                          <Cell
                            key={`opt-cell-${index}`}
                            fill={CHART_COLORS[index % CHART_COLORS.length]}
                          />
                        ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) =>
                        `${(Number(value) * 100).toFixed(1)}%`
                      }
                      contentStyle={{
                        backgroundColor: "hsl(var(--popover))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--popover-foreground))",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Allocation Changes */}
            <Card>
              <CardHeader>
                <CardTitle>Rebalancing Actions</CardTitle>
              </CardHeader>
              <CardContent>
                {optimization.allocations.filter((a) => a.action !== "hold").length > 0 ? (
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {optimization.allocations
                      .filter((a) => a.action !== "hold")
                      .sort((a, b) => Math.abs(b.weight_change) - Math.abs(a.weight_change))
                      .map((alloc, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between rounded-lg border border-border p-3"
                        >
                          <div>
                            <p className="font-medium">{alloc.symbol}</p>
                            <p className="text-xs text-muted-foreground">
                              {(alloc.current_weight * 100).toFixed(1)}% &rarr;{" "}
                              {(alloc.recommended_weight * 100).toFixed(1)}%
                            </p>
                          </div>
                          <div className="text-right">
                            <span
                              className={`text-sm font-medium ${
                                alloc.action === "increase" || alloc.action === "buy"
                                  ? "text-green-400"
                                  : alloc.action === "decrease" || alloc.action === "sell"
                                  ? "text-red-400"
                                  : "text-muted-foreground"
                              }`}
                            >
                              {alloc.action.toUpperCase()}
                            </span>
                            <p className="text-xs text-muted-foreground">
                              {alloc.weight_change >= 0 ? "+" : ""}
                              {(alloc.weight_change * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="flex h-[300px] items-center justify-center text-muted-foreground">
                    Your portfolio is already well-optimized!
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
