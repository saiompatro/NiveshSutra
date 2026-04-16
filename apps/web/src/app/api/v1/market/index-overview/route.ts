import { NextResponse } from "next/server";

import { getQuoteWithFallback } from "@/lib/server/market-data";
import { createSupabaseAnonClient } from "@/lib/server/supabase";

export async function GET() {
  try {
    const supabase = createSupabaseAnonClient();
    const quote = await getQuoteWithFallback(supabase, "^NSEI");

    return NextResponse.json({
      nifty50_value: quote.price,
      nifty50_change: quote.change,
      nifty50_change_pct: quote.changePct,
      provider: quote.provider,
    });
  } catch (error) {
    return NextResponse.json(
      { detail: error instanceof Error ? error.message : "Failed to load market overview" },
      { status: 500 }
    );
  }
}
