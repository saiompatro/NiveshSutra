from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID, DEFAULT_USER_EMAIL
from backend.models.db_models import Profile, Holding, PortfolioOptimization, OptimizationAllocation
from ..models.portfolio import MonteCarloRiskRequest, OptimizeRequest
from ..services.market_data import fetch_live_quotes_batch, get_quote_with_fallback
from math_engine.risk import MonteCarloRiskError, get_india_risk_free_rate, run_monte_carlo_var

router = APIRouter()


@router.post("/portfolio/optimize")
async def optimize_portfolio(body: OptimizeRequest, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID

    profile = db.query(Profile).filter(Profile.id == user_id).first()

    risk_profile = body.method_override or (
        profile.risk_profile if profile else None
    ) or "moderate"
    if risk_profile not in {"conservative", "moderate", "aggressive"}:
        risk_profile = "moderate"

    if not profile:
        profile = Profile(
            id=user_id,
            email=DEFAULT_USER_EMAIL,
            risk_profile=risk_profile,
        )
        db.add(profile)
        db.commit()

    holdings = (
        db.query(Holding)
        .filter(Holding.user_id == user_id)
        .all()
    )
    holdings_data = [
        {"symbol": h.symbol, "quantity": h.quantity, "avg_buy_price": h.avg_buy_price}
        for h in holdings
    ]

    # Store optimization request
    method_map = {"conservative": "min_volatility", "moderate": "max_sharpe", "aggressive": "efficient_return"}
    opt = PortfolioOptimization(
        user_id=user_id,
        risk_profile=risk_profile,
        optimization_method=method_map.get(risk_profile, "max_sharpe"),
        target_return=body.target_return,
        target_risk=body.target_risk,
        status="pending",
    )
    db.add(opt)
    db.commit()
    db.refresh(opt)
    opt_id = opt.id

    # Try running the ML optimizer inline (PyPortfolioOpt)
    if opt_id and holdings_data:
        try:
            from math_engine.optimizer import run_optimization
            opt_result = run_optimization(user_id, risk_profile, opt_id, db=db)
            return {
                "optimization_id": opt_id,
                "risk_profile": risk_profile,
                "holdings_count": len(holdings_data),
                "status": "completed",
                "expected_return": opt_result.get("expected_return"),
                "expected_risk": opt_result.get("expected_risk"),
                "sharpe_ratio": opt_result.get("sharpe_ratio"),
                "allocations": opt_result.get("allocations", []),
            }
        except Exception:
            # ML dependencies not available -- return pending for frontend fallback
            pass

    return {
        "optimization_id": opt_id,
        "risk_profile": risk_profile,
        "holdings_count": len(holdings_data),
        "status": "pending",
    }


@router.post("/portfolio/risk")
async def portfolio_monte_carlo_risk(body: MonteCarloRiskRequest, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    holdings_data = [
        {"symbol": h.symbol, "quantity": h.quantity, "avg_buy_price": h.avg_buy_price}
        for h in holdings
    ]
    try:
        return run_monte_carlo_var(
            db,
            holdings_data,
            scenarios=body.scenarios,
            horizon_days=body.horizon_days,
            lookback_days=body.lookback_days,
            confidence_levels=body.confidence_levels,
            risk_free_rate=body.risk_free_rate if body.risk_free_rate is not None else get_india_risk_free_rate(),
            seed=body.seed,
            sampling_method=body.sampling_method,
            importance_sampling=body.importance_sampling,
            importance_shift=body.importance_shift,
        )
    except MonteCarloRiskError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/portfolio/optimizations")
async def list_optimizations(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    opts = (
        db.query(PortfolioOptimization)
        .options(joinedload(PortfolioOptimization.allocations))
        .filter(PortfolioOptimization.user_id == user_id)
        .order_by(PortfolioOptimization.created_at.desc())
        .limit(10)
        .all()
    )
    return [row_to_dict(o, rels=["allocations"]) for o in opts]


@router.get("/portfolio/optimizations/{opt_id}")
async def get_optimization(opt_id: str, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    opt = (
        db.query(PortfolioOptimization)
        .options(joinedload(PortfolioOptimization.allocations))
        .filter(
            PortfolioOptimization.id == opt_id,
            PortfolioOptimization.user_id == user_id,
        )
        .first()
    )
    if not opt:
        return None
    return row_to_dict(opt, rels=["allocations"])


@router.get("/portfolio/performance")
async def portfolio_performance(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    if not holdings:
        return {"total_invested": 0, "current_value": 0, "pnl": 0, "pnl_pct": 0, "holdings": []}

    enriched = []
    total_invested = 0
    current_value = 0
    quote_map = fetch_live_quotes_batch({h.symbol: None for h in holdings})
    for h in holdings:
        try:
            quote = quote_map.get(h.symbol) or get_quote_with_fallback(db, h.symbol)
            price = quote.price
        except Exception:
            price = float(h.avg_buy_price)
        invested = float(h.quantity) * float(h.avg_buy_price)
        value = float(h.quantity) * price
        total_invested += invested
        current_value += value
        enriched.append({
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_buy_price": h.avg_buy_price,
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
