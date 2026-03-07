"""Options chain data fetching via yfinance."""
from __future__ import annotations
import yfinance as yf
from datetime import datetime


def get_available_expirations(ticker: str) -> list[str]:
    """Get available expiration dates for a ticker's options."""
    stock = yf.Ticker(ticker)
    try:
        return list(stock.options)
    except Exception:
        return []


def get_options_chain(ticker: str, expiry_date: str) -> dict:
    """Get full options chain for a ticker and expiry date.

    Returns dict with 'calls' and 'puts' lists.
    """
    stock = yf.Ticker(ticker)
    chain = stock.option_chain(expiry_date)

    def parse_options(df) -> list[dict]:
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "strike": float(row["strike"]),
                "lastPrice": float(row.get("lastPrice", 0)),
                "bid": float(row.get("bid", 0)),
                "ask": float(row.get("ask", 0)),
                "volume": int(row.get("volume", 0)) if row.get("volume") and not _is_nan(row["volume"]) else 0,
                "openInterest": int(row.get("openInterest", 0)) if row.get("openInterest") and not _is_nan(row["openInterest"]) else 0,
                "impliedVolatility": float(row.get("impliedVolatility", 0)),
                "inTheMoney": bool(row.get("inTheMoney", False)),
            })
        return rows

    return {
        "calls": parse_options(chain.calls),
        "puts": parse_options(chain.puts),
        "expiry_date": expiry_date,
    }


def get_chain_summary(ticker: str, expiry_date: str, num_strikes: int = 10) -> dict:
    """Get condensed chain: ATM +/- num_strikes strikes for AI context."""
    from app.services.market_data_service import get_quote

    quote = get_quote(ticker)
    spot = quote["price"]

    chain = get_options_chain(ticker, expiry_date)

    def filter_near_atm(options: list[dict]) -> list[dict]:
        sorted_opts = sorted(options, key=lambda o: abs(o["strike"] - spot))
        return sorted(sorted_opts[:num_strikes * 2], key=lambda o: o["strike"])

    return {
        "ticker": ticker,
        "spot_price": spot,
        "expiry_date": expiry_date,
        "calls": filter_near_atm(chain["calls"]),
        "puts": filter_near_atm(chain["puts"]),
    }


def _is_nan(value) -> bool:
    try:
        import math
        return math.isnan(float(value))
    except (ValueError, TypeError):
        return False
