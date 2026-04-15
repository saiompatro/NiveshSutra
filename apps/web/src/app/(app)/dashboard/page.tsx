"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchPortfolioPerformance,
  fetchSignals as fetchSignalsApi,
  fetchAlerts as fetchAlertsApi,
  fetchWatchlist as fetchWatchlistApi,
  fetchMarketSentiment,
  fetchMarketOverview,
} from "@/lib/api";
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
  TrendingUp,
  TrendingDown,
  Bell,
  Eye,
  BarChart3,
  Activity,
  Briefcase,
  Zap,
} from "lucide-react";
import Link from "next/link";

interface PortfolioPerformance {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_pct: number;
}

interface Signal {
  symbol: string;
  signal: string;
  confidence: number;
  created_at: string;
}

interface Alert {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface WatchlistItem {
  symbol: string;
  company_name: string;
  current_price: number;
  change_pct: number;
}

interface MarketSentiment {
  overall_sentiment: string;
  score: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
}

interface MarketOverview {
  nifty50_value: number;
  nifty50_change: number;
  nifty50_change_pct: number;
}

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

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<PortfolioPerformance | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [
        portfolioRes,
        signalsRes,
        alertsRes,
        watchlistRes,
        sentimentRes,
        marketRes,
      ] = await Promise.allSettled([
        fetchPortfolioPerformance(),
        fetchSignalsApi(),
        fetchAlertsApi(10),
        fetchWatchlistApi(),
        fetchMarketSentiment(),
        fetchMarketOverview(),
      ]);

      if (portfolioRes.status === "fulfilled") setPortfolio(portfolioRes.value);
      if (signalsRes.status === "fulfilled") setSignals(signalsRes.value.slice(0, 5));
      if (alertsRes.status === "fulfilled") setAlerts(alertsRes.value);
      if (watchlistRes.status === "fulfilled") setWatchlist(watchlistRes.value);
      if (sentimentRes.status === "fulfilled") setSentiment(sentimentRes.value);
      if (marketRes.status === "fulfilled") setMarket(marketRes.value);
    } catch {
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Your portfolio overview and market insights
        </p>
      </div>

      {/* Top row - Portfolio + Market */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Portfolio Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              Portfolio Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            {portfolio ? (
              <div className="space-y-2">
                <p className="text-3xl font-bold">
                  {formatCurrency(portfolio.total_value)}
                </p>
                <div className="flex items-center gap-2">
                  {portfolio.total_pnl >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <span
                    className={
                      portfolio.total_pnl >= 0
                        ? "text-green-400"
                        : "text-red-400"
                    }
                  >
                    {formatCurrency(portfolio.total_pnl)} (
                    {portfolio.total_pnl_pct >= 0 ? "+" : ""}
                    {portfolio.total_pnl_pct.toFixed(2)}%)
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Invested: {formatCurrency(portfolio.total_invested)}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-lg text-muted-foreground">No holdings yet</p>
                <Link
                  href="/portfolio"
                  className="text-sm text-primary hover:underline"
                >
                  Add your first holding
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Nifty 50 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Nifty 50
            </CardTitle>
          </CardHeader>
          <CardContent>
            {market ? (
              <div className="space-y-2">
                <p className="text-3xl font-bold">
                  {market.nifty50_value.toLocaleString("en-IN", {
                    maximumFractionDigits: 2,
                  })}
                </p>
                <div className="flex items-center gap-2">
                  {market.nifty50_change >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <span
                    className={
                      market.nifty50_change >= 0
                        ? "text-green-400"
                        : "text-red-400"
                    }
                  >
                    {market.nifty50_change >= 0 ? "+" : ""}
                    {market.nifty50_change.toFixed(2)} (
                    {market.nifty50_change_pct >= 0 ? "+" : ""}
                    {market.nifty50_change_pct.toFixed(2)}%)
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Market data unavailable
              </p>
            )}
          </CardContent>
        </Card>

        {/* Market Sentiment */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Market Sentiment
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sentiment ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span
                    className={`text-2xl font-bold ${
                      sentiment.overall_sentiment === "bullish"
                        ? "text-green-400"
                        : sentiment.overall_sentiment === "bearish"
                          ? "text-red-400"
                          : "text-yellow-400"
                    }`}
                  >
                    {sentiment.overall_sentiment.charAt(0).toUpperCase() +
                      sentiment.overall_sentiment.slice(1)}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    ({(sentiment.score * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="flex gap-4 text-xs">
                  <span className="text-green-400">
                    Bullish: {sentiment.bullish_count}
                  </span>
                  <span className="text-yellow-400">
                    Neutral: {sentiment.neutral_count}
                  </span>
                  <span className="text-red-400">
                    Bearish: {sentiment.bearish_count}
                  </span>
                </div>
                {/* Sentiment gauge bar */}
                <div className="flex h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="bg-green-500 transition-all"
                    style={{
                      width: `${(sentiment.bullish_count / (sentiment.bullish_count + sentiment.neutral_count + sentiment.bearish_count)) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-yellow-500 transition-all"
                    style={{
                      width: `${(sentiment.neutral_count / (sentiment.bullish_count + sentiment.neutral_count + sentiment.bearish_count)) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-red-500 transition-all"
                    style={{
                      width: `${(sentiment.bearish_count / (sentiment.bullish_count + sentiment.neutral_count + sentiment.bearish_count)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Sentiment data unavailable
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bottom row */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Top Signals */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Latest Signals
            </CardTitle>
            <CardDescription>
              <Link href="/signals" className="text-primary hover:underline">
                View all
              </Link>
            </CardDescription>
          </CardHeader>
          <CardContent>
            {signals.length > 0 ? (
              <div className="space-y-3">
                {signals.map((s, i) => (
                  <Link
                    key={i}
                    href={`/stocks/${s.symbol}`}
                    className="flex items-center justify-between rounded-lg p-2 transition-colors hover:bg-muted"
                  >
                    <div>
                      <p className="font-medium">{s.symbol}</p>
                      <p className="text-xs text-muted-foreground">
                        Confidence: {(s.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                    <Badge className={signalColor(s.signal)}>
                      {formatSignal(s.signal)}
                    </Badge>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No signals available
              </p>
            )}
          </CardContent>
        </Card>

        {/* Watchlist */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Watchlist
            </CardTitle>
          </CardHeader>
          <CardContent>
            {watchlist.length > 0 ? (
              <div className="space-y-3">
                {watchlist.map((item) => (
                  <Link
                    key={item.symbol}
                    href={`/stocks/${item.symbol}`}
                    className="flex items-center justify-between rounded-lg p-2 transition-colors hover:bg-muted"
                  >
                    <div>
                      <p className="font-medium">{item.symbol}</p>
                      <p className="text-xs text-muted-foreground truncate max-w-[120px]">
                        {item.company_name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">
                        {item.current_price.toLocaleString("en-IN", {
                          maximumFractionDigits: 2,
                        })}
                      </p>
                      <p
                        className={`text-xs ${
                          item.change_pct >= 0
                            ? "text-green-400"
                            : "text-red-400"
                        }`}
                      >
                        {item.change_pct >= 0 ? "+" : ""}
                        {item.change_pct.toFixed(2)}%
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  Your watchlist is empty
                </p>
                <Link
                  href="/stocks"
                  className="text-sm text-primary hover:underline"
                >
                  Browse stocks
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Alerts Feed */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            {alerts.length > 0 ? (
              <div className="space-y-3">
                {alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className={`rounded-lg border p-3 text-sm ${
                      alert.is_read
                        ? "border-border bg-transparent"
                        : "border-primary/20 bg-primary/5"
                    }`}
                  >
                    <p className="font-medium">{alert.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {alert.message}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Date(alert.created_at).toLocaleDateString("en-IN")}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No alerts</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-48" />
        <Skeleton className="mt-2 h-4 w-72" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent className="space-y-2">
              <Skeleton className="h-8 w-40" />
              <Skeleton className="h-4 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent className="space-y-3">
              {[1, 2, 3].map((j) => (
                <Skeleton key={j} className="h-12 w-full" />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
