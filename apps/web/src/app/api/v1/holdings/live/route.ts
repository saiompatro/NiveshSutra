import { NextRequest, NextResponse } from "next/server";

import { fetchLiveQuotesBatch, getQuoteWithFallback } from "@/lib/server/market-data";
import { createSupabaseAnonClient, requireSupabaseUser } from "@/lib/server/supabase";

export async function GET(request: NextRequest) {
  try {
    const { user } = await requireSupabaseUser(request.headers.get("authorization"));
    const supabase = createSupabaseAnonClient();

    const { data: holdings, error } = await supabase
      .from("holdings")
      .select("id, symbol, quantity, avg_buy_price, buy_date, notes, stocks(yf_ticker)")
      .eq("user_id", user.id);

    if (error) throw new Error(error.message);

    const quoteMap = await fetchLiveQuotesBatch(
      Object.fromEntries(
        (holdings ?? []).map((holding) => {
          const stockInfo = Array.isArray(holding.stocks) ? holding.stocks[0] : holding.stocks;
          return [holding.symbol, stockInfo?.yf_ticker];
        })
      )
    );

    const enriched = await Promise.all(
      (holdings ?? []).map(async (holding) => {
        const stockInfo = Array.isArray(holding.stocks) ? holding.stocks[0] : holding.stocks;
        const quote =
          quoteMap[holding.symbol] ??
          (await getQuoteWithFallback(supabase, holding.symbol, stockInfo?.yf_ticker));
        const quantity = Number(holding.quantity ?? 0);
        const avgPrice = Number(holding.avg_buy_price ?? 0);
        const value = quote.price * quantity;
        const invested = avgPrice * quantity;
        const pnl = value - invested;
        const pnlPct = invested ? (pnl / invested) * 100 : 0;

        return {
          id: holding.id,
          symbol: holding.symbol,
          quantity,
          avg_price: avgPrice,
          current_price: quote.price,
          pnl,
          pnl_pct: pnlPct,
          value,
          provider: quote.provider,
        };
      })
    );

    return NextResponse.json(enriched);
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to load holdings" },
      { status: 401 }
    );
  }
}
