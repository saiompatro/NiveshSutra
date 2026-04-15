from fastapi import APIRouter, Depends, Query
from supabase import Client
from ..dependencies import get_supabase_client

router = APIRouter()


@router.get("/signals")
async def list_signals(
    signal_type: str | None = None,
    supabase: Client = Depends(get_supabase_client),
):
    query = supabase.table("signals").select("*").order("date", desc=True).limit(50)
    if signal_type:
        query = query.eq("signal", signal_type)
    result = query.execute()

    # Deduplicate to latest per symbol
    seen = set()
    latest = []
    for row in result.data:
        if row["symbol"] not in seen:
            seen.add(row["symbol"])
            latest.append(row)
    return latest


@router.get("/signals/summary")
async def signals_summary(supabase: Client = Depends(get_supabase_client)):
    result = supabase.table("signals").select("symbol, signal, date").order("date", desc=True).limit(200).execute()
    seen = {}
    for row in result.data:
        if row["symbol"] not in seen:
            seen[row["symbol"]] = row["signal"]
    counts = {}
    for signal in seen.values():
        counts[signal] = counts.get(signal, 0) + 1
    return {"counts": counts, "total": len(seen)}


@router.get("/signals/{symbol}")
async def get_signal_history(
    symbol: str,
    days: int = Query(default=30, le=90),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("signals")
        .select("*")
        .eq("symbol", symbol)
        .order("date", desc=True)
        .limit(days)
        .execute()
    )
    return sorted(result.data, key=lambda x: x["date"])


@router.get("/signals/{symbol}/latest")
async def get_latest_signal(symbol: str, supabase: Client = Depends(get_supabase_client)):
    result = (
        supabase.table("signals")
        .select("*")
        .eq("symbol", symbol)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
