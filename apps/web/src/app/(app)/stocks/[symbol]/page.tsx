"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import {
  fetchStockDetail,
  fetchOhlcv,
  fetchIndicators,
  fetchStockSentiment,
  fetchStockNews,
  fetchLatestSignal,
  fetchWatchlistSymbols,
  addToWatchlist,
  removeFromWatchlist,
  acceptSignal as acceptSignalApi,
  fetchAcceptedSignals,
} from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp,
  TrendingDown,
  Star,
  StarOff,
  Newspaper,
  Activity,
  BarChart3,
  Loader2,
  Check,
} from "lucide-react";

interface StockInfo {
  symbol: string;
  company_name: string;
  sector: string;
  current_price: number;
  change_pct: number;
  change: number;
  day_high: number;
  day_low: number;
  volume: number;
  market_cap: number;
}

interface OhlcvCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Indicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  sma_20: number;
  sma_50: number;
  ema_12: number;
  ema_26: number;
}

interface Sentiment {
  overall: string;
  score: number;
  positive: number;
  negative: number;
  neutral: number;
}

interface NewsItem {
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: string;
}

interface Signal {
  signal: string;
  confidence: number;
  technical_score: number;
  sentiment_score: number;
  momentum_score: number;
  created_at: string;
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

const TIME_RANGES = [
  { label: "1D", days: 1 },
  { label: "5D", days: 5 },
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "1Y", days: 365 },
  { label: "ALL", days: 3650 },
] as const;

function formatLargeNumber(n: number): string {
  if (n >= 1e7) return (n / 1e7).toFixed(2) + " Cr";
  if (n >= 1e5) return (n / 1e5).toFixed(2) + " L";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toLocaleString("en-IN");
}

export default function StockDetailPage() {
  const params = useParams();
  const symbol = params.symbol as string;
  const chartRef = useRef<HTMLDivElement>(null);

  const [stock, setStock] = useState<StockInfo | null>(null);
  const [ohlcv, setOhlcv] = useState<OhlcvCandle[]>([]);
  const [indicators, setIndicators] = useState<Indicators | null>(null);
  const [sentiment, setSentiment] = useState<Sentiment | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [loading, setLoading] = useState(true);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [selectedRange, setSelectedRange] = useState("1Y");
  const [chartLoading, setChartLoading] = useState(false);
  const [isSignalAccepted, setIsSignalAccepted] = useState(false);
  const [acceptingSignal, setAcceptingSignal] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [stockRes, ohlcvRes, indicatorsRes, sentimentRes, newsRes, signalRes, watchlistRes] =
        await Promise.allSettled([
          fetchStockDetail(symbol),
          fetchOhlcv(symbol),
          fetchIndicators(symbol),
          fetchStockSentiment(symbol),
          fetchStockNews(symbol),
          fetchLatestSignal(symbol),
          fetchWatchlistSymbols(),
        ]);

      if (stockRes.status === "fulfilled" && stockRes.value) setStock(stockRes.value);
      if (ohlcvRes.status === "fulfilled") setOhlcv(ohlcvRes.value);
      if (indicatorsRes.status === "fulfilled") setIndicators(indicatorsRes.value);
      if (sentimentRes.status === "fulfilled") setSentiment(sentimentRes.value);
      if (newsRes.status === "fulfilled") setNews(newsRes.value);
      if (signalRes.status === "fulfilled") setSignal(signalRes.value);
      if (watchlistRes.status === "fulfilled") {
        setInWatchlist(watchlistRes.value.some((s) => s === symbol));
      }

      // Check if signal is already accepted
      try {
        const accepted = await fetchAcceptedSignals();
        setIsSignalAccepted(accepted.some((a) => a.symbol === symbol && a.status === "active"));
      } catch {
        // Non-critical
      }
    } catch {
      toast.error("Failed to load stock data");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleAcceptSignal() {
    if (!signal) return;
    setAcceptingSignal(true);
    try {
      await acceptSignalApi({
        symbol,
        signal_type: signal.signal,
        signal_date: signal.created_at,
        composite_score: signal.confidence,
      });
      setIsSignalAccepted(true);
      toast.success(`Now tracking ${symbol} signal for email alerts`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to accept signal");
    } finally {
      setAcceptingSignal(false);
    }
  }

  async function handleRangeChange(label: string, days: number) {
    setSelectedRange(label);
    setChartLoading(true);
    try {
      const data = await fetchOhlcv(symbol, days);
      setOhlcv(data);
    } catch {
      toast.error("Failed to load chart data");
    } finally {
      setChartLoading(false);
    }
  }

  // Candlestick chart with lightweight-charts
  useEffect(() => {
    if (!chartRef.current || ohlcv.length === 0) return;

    let chart: ReturnType<typeof import("lightweight-charts").createChart> | null = null;

    async function renderChart() {
      const { createChart, CandlestickSeries, HistogramSeries } = await import(
        "lightweight-charts"
      );

      if (!chartRef.current) return;

      // Clear previous chart
      chartRef.current.innerHTML = "";

      chart = createChart(chartRef.current, {
        width: chartRef.current.clientWidth,
        height: 400,
        layout: {
          background: { color: "transparent" },
          textColor: "#9ca3af",
        },
        grid: {
          vertLines: { color: "rgba(255,255,255,0.05)" },
          horzLines: { color: "rgba(255,255,255,0.05)" },
        },
        crosshair: {
          mode: 0,
        },
        timeScale: {
          borderColor: "rgba(255,255,255,0.1)",
        },
        rightPriceScale: {
          borderColor: "rgba(255,255,255,0.1)",
        },
      });

      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderUpColor: "#22c55e",
        borderDownColor: "#ef4444",
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
      });

      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
      });

      chart.priceScale("volume").applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });

      const candleData = ohlcv.map((c) => ({
        time: c.time as import("lightweight-charts").Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));

      const volumeData = ohlcv.map((c) => ({
        time: c.time as import("lightweight-charts").Time,
        value: c.volume,
        color: c.close >= c.open ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)",
      }));

      candleSeries.setData(candleData);
      volumeSeries.setData(volumeData);
      chart.timeScale().fitContent();

      // Handle resize
      const resizeObserver = new ResizeObserver(() => {
        if (chartRef.current && chart) {
          chart.applyOptions({ width: chartRef.current.clientWidth });
        }
      });
      resizeObserver.observe(chartRef.current);

      return () => resizeObserver.disconnect();
    }

    renderChart();

    return () => {
      if (chart) chart.remove();
    };
  }, [ohlcv]);

  async function toggleWatchlist() {
    setWatchlistLoading(true);
    try {
      if (inWatchlist) {
        await removeFromWatchlist(symbol);
        setInWatchlist(false);
        toast.success(`${symbol} removed from watchlist`);
      } else {
        await addToWatchlist(symbol);
        setInWatchlist(true);
        toast.success(`${symbol} added to watchlist`);
      }
    } catch {
      toast.error("Failed to update watchlist");
    } finally {
      setWatchlistLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-[400px] w-full" />
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stock Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{symbol}</h1>
            {stock?.sector && (
              <Badge variant="secondary">{stock.sector}</Badge>
            )}
          </div>
          {stock && (
            <>
              <p className="text-sm text-muted-foreground">
                {stock.company_name}
              </p>
              <div className="mt-2 flex items-center gap-3">
                <span className="text-3xl font-bold">
                  {stock.current_price.toLocaleString("en-IN", {
                    style: "currency",
                    currency: "INR",
                  })}
                </span>
                <span
                  className={`flex items-center gap-1 text-lg ${
                    stock.change_pct >= 0 ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {stock.change_pct >= 0 ? (
                    <TrendingUp className="h-5 w-5" />
                  ) : (
                    <TrendingDown className="h-5 w-5" />
                  )}
                  {stock.change >= 0 ? "+" : ""}
                  {stock.change.toFixed(2)} ({stock.change_pct >= 0 ? "+" : ""}
                  {stock.change_pct.toFixed(2)}%)
                </span>
              </div>
            </>
          )}
        </div>
        <Button
          variant={inWatchlist ? "secondary" : "outline"}
          onClick={toggleWatchlist}
          disabled={watchlistLoading}
        >
          {inWatchlist ? (
            <StarOff className="mr-2 h-4 w-4" />
          ) : (
            <Star className="mr-2 h-4 w-4" />
          )}
          {inWatchlist ? "Remove from Watchlist" : "Add to Watchlist"}
        </Button>
      </div>

      {/* Stock stats row */}
      {stock && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-border p-3">
            <p className="text-xs text-muted-foreground">Day High</p>
            <p className="text-lg font-semibold">
              {stock.day_high?.toLocaleString("en-IN", { maximumFractionDigits: 2 }) ?? "-"}
            </p>
          </div>
          <div className="rounded-lg border border-border p-3">
            <p className="text-xs text-muted-foreground">Day Low</p>
            <p className="text-lg font-semibold">
              {stock.day_low?.toLocaleString("en-IN", { maximumFractionDigits: 2 }) ?? "-"}
            </p>
          </div>
          <div className="rounded-lg border border-border p-3">
            <p className="text-xs text-muted-foreground">Volume</p>
            <p className="text-lg font-semibold">
              {stock.volume ? formatLargeNumber(stock.volume) : "-"}
            </p>
          </div>
          <div className="rounded-lg border border-border p-3">
            <p className="text-xs text-muted-foreground">Market Cap</p>
            <p className="text-lg font-semibold">
              {stock.market_cap ? formatLargeNumber(stock.market_cap) : "-"}
            </p>
          </div>
        </div>
      )}

      {/* Candlestick Chart */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Price Chart
            </CardTitle>
            <div className="flex gap-1">
              {TIME_RANGES.map((range) => (
                <Button
                  key={range.label}
                  variant={selectedRange === range.label ? "default" : "ghost"}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => handleRangeChange(range.label, range.days)}
                  disabled={chartLoading}
                >
                  {range.label}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div ref={chartRef} className="w-full" />
            {chartLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-background/60">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
          {!chartLoading && ohlcv.length === 0 && (
            <p className="py-20 text-center text-muted-foreground">
              No chart data available for this time range
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Technical Indicators */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Technical Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            {indicators ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">RSI (14)</p>
                  <p
                    className={`text-lg font-semibold ${
                      indicators.rsi > 70
                        ? "text-red-400"
                        : indicators.rsi < 30
                          ? "text-green-400"
                          : "text-foreground"
                    }`}
                  >
                    {indicators.rsi.toFixed(2)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {indicators.rsi > 70
                      ? "Overbought"
                      : indicators.rsi < 30
                        ? "Oversold"
                        : "Neutral"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">MACD</p>
                  <p className="text-lg font-semibold">
                    {indicators.macd.toFixed(2)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Signal: {indicators.macd_signal.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">
                    Bollinger Upper
                  </p>
                  <p className="text-lg font-semibold">
                    {indicators.bb_upper.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">
                    Bollinger Lower
                  </p>
                  <p className="text-lg font-semibold">
                    {indicators.bb_lower.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">SMA 20</p>
                  <p className="text-lg font-semibold">
                    {indicators.sma_20.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">SMA 50</p>
                  <p className="text-lg font-semibold">
                    {indicators.sma_50.toFixed(2)}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">Indicator data unavailable</p>
            )}
          </CardContent>
        </Card>

        {/* Signal Card */}
        <Card>
          <CardHeader>
            <CardTitle>Signal Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            {signal ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Overall Signal
                  </span>
                  <Badge className={`text-base ${signalColor(signal.signal)}`}>
                    {formatSignal(signal.signal)}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Confidence
                  </span>
                  <span className="font-semibold">
                    {(signal.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Technical</span>
                      <span>{(signal.technical_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-blue-500 transition-all"
                        style={{ width: `${signal.technical_score * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Sentiment</span>
                      <span>{(signal.sentiment_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-purple-500 transition-all"
                        style={{ width: `${signal.sentiment_score * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Momentum</span>
                      <span>{(signal.momentum_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-amber-500 transition-all"
                        style={{ width: `${signal.momentum_score * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Last updated:{" "}
                  {new Date(signal.created_at).toLocaleString("en-IN")}
                </p>
                <div className="pt-2">
                  {isSignalAccepted ? (
                    <Button variant="outline" disabled className="w-full gap-2">
                      <Check className="h-4 w-4 text-green-400" />
                      Tracking for Alerts
                    </Button>
                  ) : (
                    <Button
                      className="w-full"
                      onClick={handleAcceptSignal}
                      disabled={acceptingSignal}
                    >
                      {acceptingSignal && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Accept Signal
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">No signal data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Sentiment */}
        <Card>
          <CardHeader>
            <CardTitle>Sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            {sentiment ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`text-2xl font-bold ${
                      sentiment.overall === "positive"
                        ? "text-green-400"
                        : sentiment.overall === "negative"
                          ? "text-red-400"
                          : "text-yellow-400"
                    }`}
                  >
                    {sentiment.overall.charAt(0).toUpperCase() +
                      sentiment.overall.slice(1)}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    Score: {(sentiment.score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex h-3 overflow-hidden rounded-full bg-muted">
                  <div
                    className="bg-green-500"
                    style={{
                      width: `${(sentiment.positive / (sentiment.positive + sentiment.neutral + sentiment.negative)) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-yellow-500"
                    style={{
                      width: `${(sentiment.neutral / (sentiment.positive + sentiment.neutral + sentiment.negative)) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-red-500"
                    style={{
                      width: `${(sentiment.negative / (sentiment.positive + sentiment.neutral + sentiment.negative)) * 100}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Positive: {sentiment.positive}</span>
                  <span>Neutral: {sentiment.neutral}</span>
                  <span>Negative: {sentiment.negative}</span>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">
                Sentiment data unavailable
              </p>
            )}
          </CardContent>
        </Card>

        {/* News */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Newspaper className="h-4 w-4" />
              Recent News
            </CardTitle>
          </CardHeader>
          <CardContent>
            {news.length > 0 ? (
              <div className="space-y-3">
                {news.slice(0, 5).map((item, i) => (
                  <a
                    key={i}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg p-2 transition-colors hover:bg-muted"
                  >
                    <p className="text-sm font-medium leading-tight">
                      {item.title}
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{item.source}</span>
                      <span>
                        {new Date(item.published_at).toLocaleDateString(
                          "en-IN"
                        )}
                      </span>
                      <Badge
                        className={
                          item.sentiment === "positive"
                            ? "bg-green-500/20 text-green-400"
                            : item.sentiment === "negative"
                              ? "bg-red-500/20 text-red-400"
                              : "bg-yellow-500/20 text-yellow-400"
                        }
                      >
                        {item.sentiment}
                      </Badge>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No news available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
