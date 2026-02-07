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
    """Get portfolio performance snapshots."""
    db = get_supabase()
    result = (
        db.table("portfolio_snapshots")
        .select("*")
        .eq("portfolio_id", str(portfolio_id))
        .order("date")
        .execute()
    )
    return result.data
