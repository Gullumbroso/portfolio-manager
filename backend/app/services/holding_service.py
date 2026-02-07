from uuid import UUID
from app.database import get_supabase
from app.services.market_data_service import get_batch_quotes
from app.services.portfolio_service import get_portfolio_cash


def get_holdings(portfolio_id: UUID):
    """Get holdings with live price data."""
    db = get_supabase()
    result = (
        db.table("holdings_view")
        .select("*")
        .eq("portfolio_id", str(portfolio_id))
        .execute()
    )
    holdings = result.data
    if not holdings:
        return []

    # Fetch live prices for all tickers
    tickers = [h["ticker"] for h in holdings]
    quotes = get_batch_quotes(tickers)

    enriched = []
    for h in holdings:
        ticker = h["ticker"]
        total_shares = float(h["total_shares"])
        total_cost_basis = float(h["total_cost_basis"])
        avg_cost = total_cost_basis / total_shares if total_shares > 0 else 0

        quote = quotes.get(ticker)
        current_price = quote["price"] if quote else None
        market_value = total_shares * current_price if current_price else None

        enriched.append({
            "portfolio_id": h["portfolio_id"],
            "ticker": ticker,
            "total_shares": total_shares,
            "total_cost_basis": total_cost_basis,
            "avg_cost_per_share": round(avg_cost, 2),
            "current_price": current_price,
            "market_value": round(market_value, 2) if market_value else None,
            "day_change_amount": quote["change_amount"] if quote else None,
            "day_change_percent": quote["change_percent"] if quote else None,
            "total_gain_dollars": round(market_value - total_cost_basis, 2) if market_value else None,
            "total_gain_percent": round((market_value - total_cost_basis) / total_cost_basis * 100, 2) if market_value and total_cost_basis > 0 else None,
        })
    return enriched


def get_portfolio_summary(portfolio_id: UUID):
    """
    Compute true profit:
      total_value = market_value + cash_balance
      profit = total_value - total_deposits
    """
    holdings = get_holdings(portfolio_id)
    cash_data = get_portfolio_cash(portfolio_id)

    cash_balance = cash_data["cash_balance"]
    total_deposits = cash_data["total_external_deposits"]

    market_value = sum(h["market_value"] for h in holdings if h["market_value"] is not None)
    total_value = market_value + cash_balance
    profit_dollars = total_value - total_deposits
    profit_percent = (profit_dollars / total_deposits * 100) if total_deposits > 0 else 0

    return {
        "total_value": round(total_value, 2),
        "market_value": round(market_value, 2),
        "cash_balance": round(cash_balance, 2),
        "total_deposits": round(total_deposits, 2),
        "profit_dollars": round(profit_dollars, 2),
        "profit_percent": round(profit_percent, 2),
    }
