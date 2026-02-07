from uuid import UUID
from app.database import get_supabase
from app.schemas.transaction import TransactionCreate


def list_transactions(portfolio_id: UUID, limit: int = 50, offset: int = 0):
    db = get_supabase()
    result = (
        db.table("transactions")
        .select("*")
        .eq("portfolio_id", str(portfolio_id))
        .order("transacted_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data


def create_transaction(portfolio_id: UUID, data: TransactionCreate):
    db = get_supabase()
    row = {
        "portfolio_id": str(portfolio_id),
        "type": data.type.value,
        "ticker": data.ticker,
        "shares": data.shares,
        "price_per_share": data.price_per_share,
        "amount": data.amount,
        "note": data.note,
    }
    if data.transacted_at:
        row["transacted_at"] = data.transacted_at.isoformat()
    result = db.table("transactions").insert(row).execute()
    return result.data[0]


def delete_transaction(portfolio_id: UUID, transaction_id: UUID):
    db = get_supabase()
    db.table("transactions").delete().eq("id", str(transaction_id)).eq(
        "portfolio_id", str(portfolio_id)
    ).execute()
