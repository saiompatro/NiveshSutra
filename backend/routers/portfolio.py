from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError
from supabase import Client
from ..dependencies import get_current_user, get_supabase_admin, get_supabase_for_user
from ..models.portfolio import MonteCarloRiskRequest, OptimizeRequest
from ..services.market_data import fetch_live_quotes_batch, get_quote_with_fallback
from math_engine.risk import MonteCarloRiskError, get_india_risk_free_rate, run_monte_carlo_var

router = APIRouter()


@router.post("/portfolio/optimize")
async def optimize_portfolio(
    body: OptimizeRequest,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_for_user),
):
    try:
        profile = (
            supabase.table("profiles")
            .select("risk_profile")
            .eq("id", user["id"])
            .maybe_single()
            .execute()
        )
    except APIError:
        profile = None

    risk_profile = body.method_override or (
        (profile.data or {}).get("risk_profile") if profile and profile.data else None
    ) or "moderate"
    if risk_profile not in {"conservative", "moderate", "aggressive"}:
        risk_profile = "moderate"

    if not profile or not profile.data:
        try:
            supabase.table("profiles").upsert(
                {
                    "id": user["id"],
                    "email": user.get("email") or f"{user['id']}@unknown.local",
                    "risk_profile": risk_profile,
                },
                on_conflict="id",
            ).execute()
        except APIError as exc:
            raise HTTPException(status_code=502, detail=f"Could not prepare user profile: {exc.message}") from exc

    try:
        holdings = (
            supabase.table("holdings")
            .select("symbol, quantity, avg_buy_price")
            .eq("user_id", user["id"])
            .execute()
        )
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Could not load holdings: {exc.message}") from exc

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
    try:
        result = supabase.table("portfolio_optimizations").insert(opt_data).execute()
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Could not create optimization request: {exc.message}") from exc
    opt_id = result.data[0]["id"] if result.data else None

    # Try running the ML optimizer inline (PyPortfolioOpt)
    if opt_id and holdings.data:
        try:
            from math_engine.optimizer import run_optimization
            opt_result = run_optimization(user["id"], risk_profile, opt_id, supabase=supabase)
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


@router.post("/portfolio/risk")
async def portfolio_monte_carlo_risk(
    body: MonteCarloRiskRequest,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
):
    holdings = (
        supabase.table("holdings")
        .select("symbol, quantity, avg_buy_price")
        .eq("user_id", user["id"])
        .execute()
        .data
        or []
    )
    try:
        return run_monte_carlo_var(
            supabase,
            holdings,
            scenarios=body.scenarios,
            horizon_days=body.horizon_days,
            lookback_days=body.lookback_days,
            confidence_levels=body.confidence_levels,
            risk_free_rate=body.risk_free_rate if body.risk_free_rate is not None else get_india_risk_free_rate(),
            seed=body.seed,
        )
    except MonteCarloRiskError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/portfolio/optimizations")
async def list_optimizations(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
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
    supabase: Client = Depends(get_supabase_admin),
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
    supabase: Client = Depends(get_supabase_admin),
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
    quote_map = fetch_live_quotes_batch({h["symbol"]: None for h in holdings.data})
    for h in holdings.data:
        try:
            quote = quote_map.get(h["symbol"]) or get_quote_with_fallback(supabase, h["symbol"])
            price = quote.price
        except Exception:
            price = float(h["avg_buy_price"])
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
