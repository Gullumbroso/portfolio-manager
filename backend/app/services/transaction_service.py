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
    buy_txn = result.data[0]

    # Auto-create a linked DEPOSIT when buying with external funds
    if data.type.value == "BUY" and data.auto_fund_amount > 0:
        auto_note = f"[auto:buy:{buy_txn['id']}] Auto: Cash for BUY {data.ticker}"
        deposit_row = {
            "portfolio_id": str(portfolio_id),
            "type": "DEPOSIT",
            "amount": round(data.auto_fund_amount, 2),
            "note": auto_note,
        }
        if data.transacted_at:
            deposit_row["transacted_at"] = data.transacted_at.isoformat()
        db.table("transactions").insert(deposit_row).execute()

    return buy_txn


def delete_transaction(portfolio_id: UUID, transaction_id: UUID):
    db = get_supabase()
    # If deleting a BUY, also remove its linked auto-DEPOSIT
    txn_result = (
        db.table("transactions")
        .select("type")
        .eq("id", str(transaction_id))
        .eq("portfolio_id", str(portfolio_id))
        .execute()
    )
    if txn_result.data and txn_result.data[0]["type"] == "BUY":
        prefix = f"[auto:buy:{transaction_id}]"
        db.table("transactions").delete().eq("portfolio_id", str(portfolio_id)).like(
            "note", f"{prefix}%"
        ).execute()

    db.table("transactions").delete().eq("id", str(transaction_id)).eq(
        "portfolio_id", str(portfolio_id)
    ).execute()
