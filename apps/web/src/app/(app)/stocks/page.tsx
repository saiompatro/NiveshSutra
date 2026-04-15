"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { fetchStocks as fetchStocksApi } from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { Search, TrendingUp, TrendingDown } from "lucide-react";

interface Stock {
  symbol: string;
  company_name: string;
  sector: string;
  current_price: number;
  change_pct: number;
  signal?: string;
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

export default function StocksPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const router = useRouter();

  useEffect(() => {
    async function loadStocks() {
      try {
        const data = await fetchStocksApi();
        setStocks(data);
      } catch {
        toast.error("Failed to load stocks");
      } finally {
        setLoading(false);
      }
    }
    loadStocks();
  }, []);

  const sectors = useMemo(() => {
    const s = new Set(stocks.map((st) => st.sector).filter(Boolean));
    return Array.from(s).sort();
  }, [stocks]);

  const filtered = useMemo(() => {
    return stocks.filter((s) => {
      const matchSearch =
        search === "" ||
        s.symbol.toLowerCase().includes(search.toLowerCase()) ||
        s.company_name.toLowerCase().includes(search.toLowerCase());
      const matchSector =
        sectorFilter === "all" || s.sector === sectorFilter;
      return matchSearch && matchSector;
    });
  }, [stocks, search, sectorFilter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Stocks</h1>
        <p className="text-sm text-muted-foreground">
          Nifty 50 stocks with real-time signals
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>All Stocks</CardTitle>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by name or symbol..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 w-full sm:w-64"
                />
              </div>
              <Select value={sectorFilter} onValueChange={(v) => setSectorFilter(v ?? "all")}>
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="All Sectors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sectors</SelectItem>
                  {sectors.map((sector) => (
                    <SelectItem key={sector} value={sector}>
                      {sector}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead className="hidden sm:table-cell">
                    Company
                  </TableHead>
                  <TableHead className="hidden md:table-cell">
                    Sector
                  </TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Change %</TableHead>
                  <TableHead className="text-right">Signal</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      No stocks found
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((stock) => (
                    <TableRow
                      key={stock.symbol}
                      className="cursor-pointer"
                      onClick={() => router.push(`/stocks/${stock.symbol}`)}
                    >
                      <TableCell className="font-medium">
                        {stock.symbol}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell text-muted-foreground">
                        {stock.company_name}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-muted-foreground">
                        {stock.sector}
                      </TableCell>
                      <TableCell className="text-right">
                        {stock.current_price.toLocaleString("en-IN", {
                          maximumFractionDigits: 2,
                        })}
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={`inline-flex items-center gap-1 ${
                            stock.change_pct >= 0
                              ? "text-green-400"
                              : "text-red-400"
                          }`}
                        >
                          {stock.change_pct >= 0 ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {stock.change_pct >= 0 ? "+" : ""}
                          {stock.change_pct.toFixed(2)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {stock.signal ? (
                          <Badge className={signalColor(stock.signal)}>
                            {formatSignal(stock.signal)}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
