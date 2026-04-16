import { NextRequest, NextResponse } from "next/server";

import { getQuoteWithFallback, searchInstrument } from "@/lib/server/market-data";
import { createSupabaseAnonClient } from "@/lib/server/supabase";

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ symbol: string }> }
) {
  try {
    const { symbol } = await context.params;
    const supabase = createSupabaseAnonClient();
    const normalizedSymbol = symbol.toUpperCase();

    const { data: stock, error } = await supabase
      .from("stocks")
      .select("symbol, company_name, sector, yf_ticker")
      .eq("symbol", normalizedSymbol)
      .maybeSingle();

    if (error) {
      throw new Error(error.message);
    }

    const instrument = !stock ? await searchInstrument(normalizedSymbol) : null;
    const quote = stock
      ? await getQuoteWithFallback(supabase, normalizedSymbol, stock.yf_ticker)
      : await getQuoteWithFallback(supabase, instrument?.tradingSymbol ?? normalizedSymbol);

    return NextResponse.json({
      symbol: stock?.symbol ?? instrument?.tradingSymbol ?? normalizedSymbol,
      company_name: stock?.company_name ?? instrument?.shortName ?? instrument?.name ?? normalizedSymbol,
      sector: stock?.sector ?? "Unknown",
      current_price: quote.price,
      change_pct: quote.changePct,
      change: quote.change,
      day_high: quote.high,
      day_low: quote.low,
      volume: quote.volume,
      market_cap: 0,
      provider: quote.provider,
    });
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to load stock quote" },
      { status: 404 }
    );
  }
}
