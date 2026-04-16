from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, profile, stocks, stock_search, watchlist, holdings, market, sentiment, signals, portfolio, alerts, notifications

app = FastAPI(
    title="NiveshSutra API",
    description="Indian equity wealth management platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(profile.router, prefix="/api/v1", tags=["Profile"])
app.include_router(stock_search.router, prefix="/api/v1", tags=["Stock Search"])
app.include_router(stocks.router, prefix="/api/v1", tags=["Stocks"])
app.include_router(watchlist.router, prefix="/api/v1", tags=["Watchlist"])
app.include_router(holdings.router, prefix="/api/v1", tags=["Holdings"])
app.include_router(market.router, prefix="/api/v1", tags=["Market"])
app.include_router(sentiment.router, prefix="/api/v1", tags=["Sentiment"])
app.include_router(signals.router, prefix="/api/v1", tags=["Signals"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["Portfolio"])
app.include_router(alerts.router, prefix="/api/v1", tags=["Alerts"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
