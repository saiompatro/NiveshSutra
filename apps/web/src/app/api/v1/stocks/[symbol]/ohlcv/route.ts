import { NextRequest, NextResponse } from "next/server";

import {
  fetchHistoricalDaily,
  getQuoteWithFallback,
  type HistoryBar,
  mergeLiveQuoteIntoHistory,
} from "@/lib/server/market-data";
import { createSupabaseAnonClient } from "@/lib/server/supabase";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ symbol: string }> }
) {
  try {
    const { symbol } = await context.params;
    const days = Number(request.nextUrl.searchParams.get("days") ?? "365");
    const supabase = createSupabaseAnonClient();
    const normalizedSymbol = symbol.toUpperCase();

    const { data: stock, error: stockError } = await supabase
      .from("stocks")
      .select("symbol, yf_ticker")
      .eq("symbol", normalizedSymbol)
      .maybeSingle();

    if (stockError) {
      throw new Error(stockError.message);
    }

    let rows: HistoryBar[] = await fetchHistoricalDaily(
      normalizedSymbol,
      stock?.yf_ticker,
      days
    );
    if (rows.length === 0) {
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - days);
      const { data, error } = await supabase
        .from("ohlcv")
        .select("date, open, high, low, close, volume")
        .eq("symbol", normalizedSymbol)
        .gte("date", fromDate.toISOString().slice(0, 10))
        .order("date", { ascending: true });

      if (error) throw new Error(error.message);
      rows = (data ?? []) as HistoryBar[];
    }

    if (rows.length > 0) {
      try {
        const quote = await getQuoteWithFallback(supabase, normalizedSymbol, stock?.yf_ticker);
        rows = mergeLiveQuoteIntoHistory(rows, quote);
      } catch {
        // Keep the historical series if live quote resolution fails.
      }
    }

    return NextResponse.json(rows);
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to load price history" },
      { status: 404 }
    );
  }
}
