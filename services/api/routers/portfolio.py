from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client
from ..models.portfolio import OptimizeRequest

router = APIRouter()


@router.post("/portfolio/optimize")
async def optimize_portfolio(
    body: OptimizeRequest,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    # Get user profile for risk_profile
    profile = supabase.table("profiles").select("risk_profile").eq("id", user["id"]).single().execute()
    risk_profile = body.method_override or (profile.data["risk_profile"] if profile.data else "moderate")

    # Get holdings
    holdings = supabase.table("holdings").select("symbol, quantity, avg_buy_price").eq("user_id", user["id"]).execute()

    # Store optimization request
    method_map = {"conservative": "min_volatility", "moderate": "max_sharpe", "aggressive": "efficient_return"}
    opt_data = {
        "user_id": user["id"],
        "risk_profile": risk_profile,
        "optimization_method": method_map.get(risk_profile, "max_sharpe"),
        "target_return": body.target_return,
        "target_risk": body.target_risk,
        "status": "pending",
    }
    result = supabase.table("portfolio_optimizations").insert(opt_data).execute()
    opt_id = result.data[0]["id"] if result.data else None

    # Try running the ML optimizer inline (PyPortfolioOpt)
    if opt_id and holdings.data:
        try:
            from services.ml.optimizer import run_optimization
            opt_result = run_optimization(user["id"], risk_profile, opt_id)
            return {
                "optimization_id": opt_id,
                "risk_profile": risk_profile,
                "holdings_count": len(holdings.data),
                "status": "completed",
                "expected_return": opt_result.get("expected_return"),
                "expected_risk": opt_result.get("expected_risk"),
                "sharpe_ratio": opt_result.get("sharpe_ratio"),
                "allocations": opt_result.get("allocations", []),
            }
        except Exception:
            # ML dependencies not available — return pending for frontend fallback
            pass

    return {
        "optimization_id": opt_id,
        "risk_profile": risk_profile,
        "holdings_count": len(holdings.data) if holdings.data else 0,
        "status": "pending",
    }


@router.get("/portfolio/optimizations")
async def list_optimizations(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_client)):
    result = (
        supabase.table("portfolio_optimizations")
        .select("*, optimization_allocations(*)")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    return result.data


@router.get("/portfolio/optimizations/{opt_id}")
async def get_optimization(
    opt_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("portfolio_optimizations")
        .select("*, optimization_allocations(*)")
        .eq("id", opt_id)
        .eq("user_id", user["id"])
        .single()
        .execute()
    )
    return result.data


@router.get("/portfolio/performance")
async def portfolio_performance(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    holdings = (
        supabase.table("holdings")
        .select("symbol, quantity, avg_buy_price")
        .eq("user_id", user["id"])
        .execute()
    )
    if not holdings.data:
        return {"total_invested": 0, "current_value": 0, "pnl": 0, "pnl_pct": 0, "holdings": []}

    enriched = []
    total_invested = 0
    current_value = 0
    for h in holdings.data:
        ohlcv = (
            supabase.table("ohlcv")
            .select("close")
            .eq("symbol", h["symbol"])
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        price = float(ohlcv.data[0]["close"]) if ohlcv.data else float(h["avg_buy_price"])
        invested = float(h["quantity"]) * float(h["avg_buy_price"])
        value = float(h["quantity"]) * price
        total_invested += invested
        current_value += value
        enriched.append({
            "symbol": h["symbol"],
            "quantity": h["quantity"],
            "avg_buy_price": h["avg_buy_price"],
            "current_price": price,
            "invested": round(invested, 2),
            "value": round(value, 2),
            "pnl": round(value - invested, 2),
            "pnl_pct": round(((value - invested) / invested) * 100, 2) if invested else 0,
        })

    return {
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "pnl": round(current_value - total_invested, 2),
        "pnl_pct": round(((current_value - total_invested) / total_invested) * 100, 2) if total_invested else 0,
        "holdings": enriched,
    }
