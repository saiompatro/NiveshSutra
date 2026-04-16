import { NextRequest, NextResponse } from "next/server";

import {
  fetchLiveQuotesBatch,
  getQuoteWithFallback,
} from "@/lib/server/market-data";
import { createSupabaseAnonClient } from "@/lib/server/supabase";

export async function GET(request: NextRequest) {
  try {
    const supabase = createSupabaseAnonClient();
    const nifty50Only = request.nextUrl.searchParams.get("nifty50_only") === "true";
    const sector = request.nextUrl.searchParams.get("sector");

    let query = supabase
      .from("stocks")
      .select("symbol, company_name, sector, is_nifty50, yf_ticker")
      .eq("active", true);

    if (sector) query = query.eq("sector", sector);
    if (nifty50Only) query = query.eq("is_nifty50", true);

    const [{ data: stocks, error: stocksError }, { data: signals, error: signalsError }] = await Promise.all([
      query.order("symbol"),
      supabase
        .from("signals")
        .select("symbol, signal, date")
        .order("date", { ascending: false })
        .limit(200),
    ]);

    if (stocksError) {
      throw new Error(stocksError.message);
    }
    if (signalsError) {
      throw new Error(signalsError.message);
    }

    const signalMap = new Map<string, string>();
    for (const row of signals ?? []) {
      if (!signalMap.has(row.symbol)) {
        signalMap.set(row.symbol, row.signal);
      }
    }

    const quoteMap = await fetchLiveQuotesBatch(
      Object.fromEntries((stocks ?? []).map((stock) => [stock.symbol, stock.yf_ticker]))
    );

    const enriched = await Promise.all(
      (stocks ?? []).map(async (stock) => {
        const quote = quoteMap[stock.symbol] ?? (await getQuoteWithFallback(supabase, stock.symbol, stock.yf_ticker));
        return {
          symbol: stock.symbol,
          company_name: stock.company_name ?? "",
          sector: stock.sector ?? "",
          current_price: quote.price,
          change_pct: quote.changePct,
          signal: signalMap.get(stock.symbol),
          provider: quote.provider,
        };
      })
    );

    return NextResponse.json(enriched);
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to load live stocks" },
      { status: 500 }
    );
  }
}
