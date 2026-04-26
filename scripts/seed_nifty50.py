"""
Seed script: insert all 50 Nifty 50 stocks into the stocks table.

Usage:
    python scripts/seed_nifty50.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.config import get_supabase

# ---------------------------------------------------------------------------
# Nifty 50 stock data
# ---------------------------------------------------------------------------
NIFTY_50_STOCKS = [
    {
        "symbol": "ADANIENT",
        "yf_ticker": "ADANIENT.NS",
        "company_name": "Adani Enterprises Ltd",
        "sector": "Metals & Mining",
        "market_cap_category": "large",
    },
    {
        "symbol": "ADANIPORTS",
        "yf_ticker": "ADANIPORTS.NS",
        "company_name": "Adani Ports and Special Economic Zone Ltd",
        "sector": "Infrastructure",
        "market_cap_category": "large",
    },
    {
        "symbol": "APOLLOHOSP",
        "yf_ticker": "APOLLOHOSP.NS",
        "company_name": "Apollo Hospitals Enterprise Ltd",
        "sector": "Healthcare",
        "market_cap_category": "large",
    },
    {
        "symbol": "ASIANPAINT",
        "yf_ticker": "ASIANPAINT.NS",
        "company_name": "Asian Paints Ltd",
        "sector": "Consumer Goods",
        "market_cap_category": "large",
    },
    {
        "symbol": "AXISBANK",
        "yf_ticker": "AXISBANK.NS",
        "company_name": "Axis Bank Ltd",
        "sector": "Banking",
        "market_cap_category": "large",
    },
    {
        "symbol": "BAJAJ-AUTO",
        "yf_ticker": "BAJAJ-AUTO.NS",
        "company_name": "Bajaj Auto Ltd",
        "sector": "Automobile",
        "market_cap_category": "large",
    },
    {
        "symbol": "BAJFINANCE",
        "yf_ticker": "BAJFINANCE.NS",
        "company_name": "Bajaj Finance Ltd",
        "sector": "Financial Services",
        "market_cap_category": "large",
    },
    {
        "symbol": "BAJAJFINSV",
        "yf_ticker": "BAJAJFINSV.NS",
        "company_name": "Bajaj Finserv Ltd",
        "sector": "Financial Services",
        "market_cap_category": "large",
    },
    {
        "symbol": "BHARTIARTL",
        "yf_ticker": "BHARTIARTL.NS",
        "company_name": "Bharti Airtel Ltd",
        "sector": "Telecom",
        "market_cap_category": "large",
    },
    {
        "symbol": "BPCL",
        "yf_ticker": "BPCL.NS",
        "company_name": "Bharat Petroleum Corporation Ltd",
        "sector": "Oil & Gas",
        "market_cap_category": "large",
    },
    {
        "symbol": "BRITANNIA",
        "yf_ticker": "BRITANNIA.NS",
        "company_name": "Britannia Industries Ltd",
        "sector": "FMCG",
        "market_cap_category": "large",
    },
    {
        "symbol": "CIPLA",
        "yf_ticker": "CIPLA.NS",
        "company_name": "Cipla Ltd",
        "sector": "Pharma",
        "market_cap_category": "large",
    },
    {
        "symbol": "COALINDIA",
        "yf_ticker": "COALINDIA.NS",
        "company_name": "Coal India Ltd",
        "sector": "Metals & Mining",
        "market_cap_category": "large",
    },
    {
        "symbol": "DIVISLAB",
        "yf_ticker": "DIVISLAB.NS",
        "company_name": "Divi's Laboratories Ltd",
        "sector": "Pharma",
        "market_cap_category": "large",
    },
    {
        "symbol": "DRREDDY",
        "yf_ticker": "DRREDDY.NS",
        "company_name": "Dr. Reddy's Laboratories Ltd",
        "sector": "Pharma",
        "market_cap_category": "large",
    },
    {
        "symbol": "EICHERMOT",
        "yf_ticker": "EICHERMOT.NS",
        "company_name": "Eicher Motors Ltd",
        "sector": "Automobile",
        "market_cap_category": "large",
    },
    {
        "symbol": "GRASIM",
        "yf_ticker": "GRASIM.NS",
        "company_name": "Grasim Industries Ltd",
        "sector": "Cement",
        "market_cap_category": "large",
    },
    {
        "symbol": "HCLTECH",
        "yf_ticker": "HCLTECH.NS",
        "company_name": "HCL Technologies Ltd",
        "sector": "IT",
        "market_cap_category": "large",
    },
    {
        "symbol": "HDFCBANK",
        "yf_ticker": "HDFCBANK.NS",
        "company_name": "HDFC Bank Ltd",
        "sector": "Banking",
        "market_cap_category": "large",
    },
    {
        "symbol": "HDFCLIFE",
        "yf_ticker": "HDFCLIFE.NS",
        "company_name": "HDFC Life Insurance Company Ltd",
        "sector": "Insurance",
        "market_cap_category": "large",
    },
    {
        "symbol": "HEROMOTOCO",
        "yf_ticker": "HEROMOTOCO.NS",
        "company_name": "Hero MotoCorp Ltd",
        "sector": "Automobile",
        "market_cap_category": "large",
    },
    {
        "symbol": "HINDALCO",
        "yf_ticker": "HINDALCO.NS",
        "company_name": "Hindalco Industries Ltd",
        "sector": "Metals & Mining",
        "market_cap_category": "large",
    },
    {
        "symbol": "HINDUNILVR",
        "yf_ticker": "HINDUNILVR.NS",
        "company_name": "Hindustan Unilever Ltd",
        "sector": "FMCG",
        "market_cap_category": "large",
    },
    {
        "symbol": "ICICIBANK",
        "yf_ticker": "ICICIBANK.NS",
        "company_name": "ICICI Bank Ltd",
        "sector": "Banking",
        "market_cap_category": "large",
    },
    {
        "symbol": "INDUSINDBK",
        "yf_ticker": "INDUSINDBK.NS",
        "company_name": "IndusInd Bank Ltd",
        "sector": "Banking",
        "market_cap_category": "large",
    },
    {
        "symbol": "INFY",
        "yf_ticker": "INFY.NS",
        "company_name": "Infosys Ltd",
        "sector": "IT",
        "market_cap_category": "large",
    },
    {
        "symbol": "ITC",
        "yf_ticker": "ITC.NS",
        "company_name": "ITC Ltd",
        "sector": "FMCG",
        "market_cap_category": "large",
    },
    {
        "symbol": "JSWSTEEL",
        "yf_ticker": "JSWSTEEL.NS",
        "company_name": "JSW Steel Ltd",
        "sector": "Metals & Mining",
        "market_cap_category": "large",
    },
    {
        "symbol": "KOTAKBANK",
        "yf_ticker": "KOTAKBANK.NS",
        "company_name": "Kotak Mahindra Bank Ltd",
        "sector": "Banking",
        "market_cap_category": "large",
    },
    {
        "symbol": "LT",
        "yf_ticker": "LT.NS",
        "company_name": "Larsen & Toubro Ltd",
        "sector": "Infrastructure",
        "market_cap_category": "large",
    },
    {
        "symbol": "LTIM",
        "yf_ticker": "LTIM.NS",
        "company_name": "LTIMindtree Ltd",
        "sector": "IT",
        "market_cap_category": "large",
    },
    {
        "symbol": "M&M",
        "yf_ticker": "M&M.NS",
        "company_name": "Mahindra & Mahindra Ltd",
        "sector": "Automobile",
        "market_cap_category": "large",
    },
    {
        "symbol": "MARUTI",
        "yf_ticker": "MARUTI.NS",
        "company_name": "Maruti Suzuki India Ltd",
        "sector": "Automobile",
        "market_cap_category": "large",
    },
    {
        "symbol": "NESTLEIND",
        "yf_ticker": "NESTLEIND.NS",
        "company_name": "Nestle India Ltd",
        "sector": "FMCG",
        "market_cap_category": "large",
    },
    {
        "symbol": "NTPC",
        "yf_ticker": "NTPC.NS",
        "company_name": "NTPC Ltd",
        "sector": "Power",
        "market_cap_category": "large",
    },
    {
        "symbol": "ONGC",
        "yf_ticker": "ONGC.NS",
        "company_name": "Oil and Natural Gas Corporation Ltd",
        "sector": "Oil & Gas",
        "market_cap_category": "large",
    },
    {
        "symbol": "POWERGRID",
        "yf_ticker": "POWERGRID.NS",
        "company_name": "Power Grid Corporation of India Ltd",
        "sector": "Power",
        "market_cap_category": "large",
    },
    {
        "symbol": "RELIANCE",
        "yf_ticker": "RELIANCE.NS",
        "company_name": "Reliance Industries Ltd",
        "sector": "Oil & Gas",
        "market_cap_category": "large",
    },
    {
        "symbol": "SBIN",
        "yf_ticker": "SBIN.NS",
        "company_name": "State Bank of India",
        "sector": "Banking",
        "market_cap_category": "large",
    },
    {
        "symbol": "SBILIFE",
        "yf_ticker": "SBILIFE.NS",
        "company_name": "SBI Life Insurance Company Ltd",
        "sector": "Insurance",
        "market_cap_category": "large",
    },
    {
        "symbol": "SUNPHARMA",
        "yf_ticker": "SUNPHARMA.NS",
        "company_name": "Sun Pharmaceutical Industries Ltd",
        "sector": "Pharma",
        "market_cap_category": "large",
    },
    {
        "symbol": "TATACONSUM",
        "yf_ticker": "TATACONSUM.NS",
        "company_name": "Tata Consumer Products Ltd",
        "sector": "FMCG",
        "market_cap_category": "large",
    },
    {
        "symbol": "TATAMOTORS",
        "yf_ticker": "TATAMOTORS.NS",
        "company_name": "Tata Motors Ltd",
        "sector": "Automobile",
        "market_cap_category": "large",
    },
    {
        "symbol": "TATASTEEL",
        "yf_ticker": "TATASTEEL.NS",
        "company_name": "Tata Steel Ltd",
        "sector": "Metals & Mining",
        "market_cap_category": "large",
    },
    {
        "symbol": "TCS",
        "yf_ticker": "TCS.NS",
        "company_name": "Tata Consultancy Services Ltd",
        "sector": "IT",
        "market_cap_category": "large",
    },
    {
        "symbol": "TECHM",
        "yf_ticker": "TECHM.NS",
        "company_name": "Tech Mahindra Ltd",
        "sector": "IT",
        "market_cap_category": "large",
    },
    {
        "symbol": "TITAN",
        "yf_ticker": "TITAN.NS",
        "company_name": "Titan Company Ltd",
        "sector": "Consumer Goods",
        "market_cap_category": "large",
    },
    {
        "symbol": "TRENT",
        "yf_ticker": "TRENT.NS",
        "company_name": "Trent Ltd",
        "sector": "Retail",
        "market_cap_category": "large",
    },
    {
        "symbol": "ULTRACEMCO",
        "yf_ticker": "ULTRACEMCO.NS",
        "company_name": "UltraTech Cement Ltd",
        "sector": "Cement",
        "market_cap_category": "large",
    },
    {
        "symbol": "WIPRO",
        "yf_ticker": "WIPRO.NS",
        "company_name": "Wipro Ltd",
        "sector": "IT",
        "market_cap_category": "large",
    },
]


def main():
    sb = get_supabase()
    print(f"Seeding {len(NIFTY_50_STOCKS)} Nifty 50 stocks into the stocks table...")

    # Upsert so re-running is safe
    sb.table("stocks").upsert(NIFTY_50_STOCKS, on_conflict="symbol").execute()

    print(f"Done. {len(NIFTY_50_STOCKS)} stocks upserted.")


if __name__ == "__main__":
    main()
