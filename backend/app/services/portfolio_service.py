from __future__ import annotations

from uuid import UUID
from app.database import get_supabase
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


def list_portfolios():
    db = get_supabase()
    result = db.table("portfolios").select("*").order("created_at").execute()
    return result.data


def get_portfolio(portfolio_id: UUID):
    db = get_supabase()
    result = db.table("portfolios").select("*").eq("id", str(portfolio_id)).single().execute()
    return result.data


def create_portfolio(data: PortfolioCreate):
    db = get_supabase()
    result = db.table("portfolios").insert({
        "name": data.name,
        "description": data.description,
    }).execute()
    return result.data[0]


def update_portfolio(portfolio_id: UUID, data: PortfolioUpdate):
    db = get_supabase()
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        return get_portfolio(portfolio_id)
    result = db.table("portfolios").update(update_data).eq("id", str(portfolio_id)).execute()
    return result.data[0]


def delete_portfolio(portfolio_id: UUID):
    db = get_supabase()
    db.table("portfolios").delete().eq("id", str(portfolio_id)).execute()


def get_portfolio_cash(portfolio_id: UUID):
    """Get cash balance and total deposits from the view."""
    db = get_supabase()
    result = db.table("portfolio_cash_view").select("*").eq("portfolio_id", str(portfolio_id)).execute()
    if not result.data:
        return {"cash_balance": 0.0, "total_external_deposits": 0.0}
    row = result.data[0]
    return {
        "cash_balance": float(row["cash_balance"] or 0),
        "total_external_deposits": float(row["total_external_deposits"] or 0),
    }


def get_performance(portfolio_id: UUID, period: str = "1M"):
    """Get portfolio performance — from snapshots if available, otherwise reconstructed from transactions."""
    db = get_supabase()
    result = (
        db.table("portfolio_snapshots")
        .select("*")
        .eq("portfolio_id", str(portfolio_id))
        .order("date")
        .execute()
    )
    if result.data:
        return result.data

    return _reconstruct_performance(portfolio_id, period)


def _reconstruct_performance(portfolio_id: UUID, period: str = "1M"):
    """Reconstruct daily portfolio values from transactions + historical prices."""
    from app.services.market_data_service import get_history

    # Intraday periods don't make sense for reconstruction — use daily equivalents
    if period in ("1D", "1W"):
        period = "1M"

    db = get_supabase()
    txns = (
        db.table("transactions")
        .select("*")
        .eq("portfolio_id", str(portfolio_id))
        .order("transacted_at")
        .execute()
    )
    if not txns.data:
        return []

    # Collect unique stock tickers (BUY/SELL only)
    tickers = list(set(t["ticker"] for t in txns.data if t.get("ticker")))

    # Fetch historical prices for each ticker over the requested period
    price_histories: dict[str, dict[str, float]] = {}
    for ticker in tickers:
        try:
            history = get_history(ticker, period)
            price_histories[ticker] = {p["date"]: p["close"] for p in history}
        except Exception:
            pass

    if not price_histories:
        return []

    # All trading dates from price data, starting from the first transaction
    first_txn_date = txns.data[0]["transacted_at"][:10]
    all_dates = sorted(d for d in set(d for ph in price_histories.values() for d in ph) if d >= first_txn_date)

    points = []
    for date in all_dates:
        # Replay transactions up to this date to get holdings + cash
        cash = 0.0
        total_deposits = 0.0
        holdings: dict[str, float] = {}

        for txn in txns.data:
            txn_date = txn["transacted_at"][:10]
            if txn_date > date:
                break

            txn_type = txn["type"]
            amount = float(txn.get("amount") or 0)

            if txn_type == "DEPOSIT":
                cash += amount
                total_deposits += amount
            elif txn_type == "WITHDRAWAL":
                cash -= amount
                total_deposits -= amount
            elif txn_type == "BUY":
                ticker = txn["ticker"]
                shares = float(txn.get("shares") or 0)
                holdings[ticker] = holdings.get(ticker, 0) + shares
                cash -= amount
            elif txn_type == "SELL":
                ticker = txn["ticker"]
                shares = float(txn.get("shares") or 0)
                holdings[ticker] = holdings.get(ticker, 0) - shares
                cash += amount

        # Compute market value using that day's prices
        market_value = 0.0
        for ticker, shares in holdings.items():
            if shares > 0 and ticker in price_histories:
                price = price_histories[ticker].get(date, 0)
                if price:
                    market_value += shares * price

        total_value = market_value + cash

        points.append({
            "date": date,
            "total_value": round(total_value, 2),
            "cash_balance": round(cash, 2),
            "market_value": round(market_value, 2),
            "total_deposits": round(total_deposits, 2),
            "profit": round(total_value - total_deposits, 2),
        })

    return points
