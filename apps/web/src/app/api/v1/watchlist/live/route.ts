import { NextRequest, NextResponse } from "next/server";

import { fetchLiveQuotesBatch, getQuoteWithFallback } from "@/lib/server/market-data";
import { createSupabaseAnonClient, requireSupabaseUser } from "@/lib/server/supabase";

export async function GET(request: NextRequest) {
  try {
    const { user } = await requireSupabaseUser(request.headers.get("authorization"));
    const supabase = createSupabaseAnonClient();

    const { data: rows, error } = await supabase
      .from("watchlist")
      .select("symbol, stocks(company_name, yf_ticker)")
      .eq("user_id", user.id)
      .order("added_at", { ascending: false });

    if (error) throw new Error(error.message);

    const quoteMap = await fetchLiveQuotesBatch(
      Object.fromEntries(
        (rows ?? []).map((row) => {
          const stockInfo = Array.isArray(row.stocks) ? row.stocks[0] : row.stocks;
          return [row.symbol, stockInfo?.yf_ticker];
        })
      )
    );

    const items = await Promise.all(
      (rows ?? []).map(async (row) => {
        const stockInfo = Array.isArray(row.stocks) ? row.stocks[0] : row.stocks;
        const quote =
          quoteMap[row.symbol] ??
          (await getQuoteWithFallback(supabase, row.symbol, stockInfo?.yf_ticker));
        return {
          symbol: row.symbol,
          company_name: stockInfo?.company_name ?? "",
          current_price: quote.price,
          change_pct: quote.changePct,
          provider: quote.provider,
        };
      })
    );

    return NextResponse.json(items);
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to load watchlist" },
      { status: 401 }
    );
  }
}
