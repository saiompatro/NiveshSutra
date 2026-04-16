import { NextRequest, NextResponse } from "next/server";

import {
  fetchHistoricalDaily,
  fetchLiveQuote,
  searchInstrument,
} from "@/lib/server/market-data";
import {
  createSupabaseAdminClient,
  createSupabaseAnonClient,
  createSupabaseUserClient,
  hasSupabaseServiceRole,
  requireSupabaseUser,
} from "@/lib/server/supabase";

export async function GET(request: NextRequest) {
  try {
    const { accessToken } = await requireSupabaseUser(request.headers.get("authorization"));
    const supabase = createSupabaseAnonClient();
    const admin = hasSupabaseServiceRole() ? createSupabaseAdminClient() : null;
    const writer = admin ?? createSupabaseUserClient(accessToken);

    const rawQuery = request.nextUrl.searchParams.get("q")?.trim() ?? "";
    if (!rawQuery) {
      return NextResponse.json({ detail: "Query is required" }, { status: 400 });
    }

    const normalizedSymbol = rawQuery.toUpperCase().replace(/\.(NS|NSE|BO|BSE)$/g, "");
    const { data: existingStock, error: existingError } = await supabase
      .from("stocks")
      .select("*")
      .eq("symbol", normalizedSymbol)
      .maybeSingle();

    if (existingError) {
      throw new Error(existingError.message);
    }
    if (existingStock) {
      return NextResponse.json({ stock: existingStock, source: "database" });
    }

    const instrument = await searchInstrument(rawQuery);
    await fetchLiveQuote(instrument.tradingSymbol, instrument.exchange === "BSE" ? `${instrument.tradingSymbol}.BSE` : `${instrument.tradingSymbol}.NS`);

    const stockRecord = {
      symbol: instrument.tradingSymbol.toUpperCase(),
      yf_ticker: instrument.exchange === "BSE" ? `${instrument.tradingSymbol}.BSE` : `${instrument.tradingSymbol}.NS`,
      company_name: instrument.shortName || instrument.name || instrument.tradingSymbol,
      sector: "Unknown",
      industry: "Unknown",
      market_cap_category: "unknown",
      is_nifty50: false,
      active: true,
    };

    const { data: insertedStock, error: insertError } = await writer
      .from("stocks")
      .insert(stockRecord)
      .select("*")
      .single();

    if (insertError) {
      throw new Error(
        insertError.message.includes("new row violates row-level security")
          ? "The stock was found on Upstox, but Vercel is missing SUPABASE_SERVICE_ROLE_KEY or the authenticated stock insert policy migration has not been applied."
          : insertError.message
      );
    }

    if (admin) {
      try {
        const candles = await fetchHistoricalDaily(stockRecord.symbol, stockRecord.yf_ticker, 90);
        if (candles.length > 0) {
          await admin.from("ohlcv").upsert(
            candles.map((candle) => ({
              symbol: stockRecord.symbol,
              date: candle.date,
              open: Number(candle.open.toFixed(2)),
              high: Number(candle.high.toFixed(2)),
              low: Number(candle.low.toFixed(2)),
              close: Number(candle.close.toFixed(2)),
              volume: candle.volume,
            })),
            { onConflict: "symbol,date" }
          );
        }
      } catch {
        // Live chart routes can still fetch directly from Upstox, so initial OHLCV seeding is best-effort only.
      }
    }

    return NextResponse.json({ stock: insertedStock, source: admin ? "upstox" : "upstox_user_insert" });
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Could not find stock" },
      { status: 404 }
    );
  }
}
