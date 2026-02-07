from __future__ import annotations
import yfinance as yf
import finnhub
from datetime import datetime, timezone
from app.database import get_supabase
from app.config import get_settings

# Period mapping for yfinance
PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "1W": ("5d", "30m"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "1Y": ("1y", "1d"),
    "ALL": ("max", "1wk"),
}

CACHE_TTL_SECONDS = 60


def _get_finnhub_client():
    settings = get_settings()
    if not settings.finnhub_api_key:
        return None
    return finnhub.Client(api_key=settings.finnhub_api_key)


def _get_cached_quote(ticker: str) -> dict | None:
    """Check price_cache for a fresh quote."""
    db = get_supabase()
    result = db.table("price_cache").select("*").eq("ticker", ticker).execute()
    if not result.data:
        return None
    row = result.data[0]
    fetched_at = datetime.fromisoformat(row["fetched_at"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
    if age > CACHE_TTL_SECONDS:
        return None
    return {
        "ticker": row["ticker"],
        "price": float(row["price"]),
        "change_amount": float(row["change_amount"]),
        "change_percent": float(row["change_percent"]),
    }


def _cache_quote(ticker: str, price: float, change_amount: float, change_percent: float):
    db = get_supabase()
    db.table("price_cache").upsert({
        "ticker": ticker,
        "price": price,
        "change_amount": change_amount,
        "change_percent": change_percent,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def get_quote(ticker: str) -> dict:
    """Get current quote, with caching. Uses Finnhub first, falls back to yfinance."""
    cached = _get_cached_quote(ticker)
    if cached:
        return cached

    # Try Finnhub first (more reliable, no SSL issues)
    client = _get_finnhub_client()
    if client:
        try:
            q = client.quote(ticker)
            if q and q.get("c") and q["c"] > 0:
                price = round(float(q["c"]), 2)
                prev_close = float(q.get("pc", price))
                change_amount = round(price - prev_close, 2)
                change_percent = round(float(q.get("dp", 0)), 2)
                _cache_quote(ticker, price, change_amount, change_percent)
                return {
                    "ticker": ticker,
                    "price": price,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                }
        except Exception:
            pass

    # Fallback to yfinance
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5d", interval="1d")
    if hist.empty:
        raise ValueError(f"No price data for {ticker}")

    price = round(float(hist["Close"].iloc[-1]), 2)
    prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
    change_amount = round(price - prev_close, 2)
    change_percent = round(change_amount / prev_close * 100, 2) if prev_close else 0

    _cache_quote(ticker, price, change_amount, change_percent)

    return {
        "ticker": ticker,
        "price": price,
        "change_amount": change_amount,
        "change_percent": change_percent,
    }


def get_batch_quotes(tickers: list[str]) -> dict[str, dict]:
    """Get quotes for multiple tickers. Returns dict keyed by ticker."""
    results = {}
    uncached = []
    for t in tickers:
        cached = _get_cached_quote(t)
        if cached:
            results[t] = cached
        else:
            uncached.append(t)

    if uncached:
        for t in uncached:
            try:
                results[t] = get_quote(t)
            except Exception:
                pass

    return results


def get_history(ticker: str, period: str = "1M") -> list[dict]:
    """Get historical price data."""
    yf_period, interval = PERIOD_MAP.get(period, ("1mo", "1d"))
    stock = yf.Ticker(ticker)
    hist = stock.history(period=yf_period, interval=interval)

    points = []
    for date, row in hist.iterrows():
        points.append({
            "date": date.strftime("%Y-%m-%d %H:%M") if interval in ("5m", "30m") else date.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })
    return points


def get_news(ticker: str) -> list[dict]:
    """Get news articles for a ticker from Finnhub."""
    client = _get_finnhub_client()
    if not client:
        return []

    from datetime import timedelta
    now = datetime.now()
    from_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    to_date = now.strftime("%Y-%m-%d")

    try:
        news = client.company_news(ticker, _from=from_date, to=to_date)
        return [
            {
                "headline": n.get("headline", ""),
                "summary": n.get("summary", ""),
                "source": n.get("source", ""),
                "url": n.get("url", ""),
                "image": n.get("image"),
                "datetime": n.get("datetime", 0),
            }
            for n in news[:20]
        ]
    except Exception:
        return []
