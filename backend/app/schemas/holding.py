from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID


class HoldingResponse(BaseModel):
    portfolio_id: UUID
    ticker: str
    total_shares: float
    total_cost_basis: float
    avg_cost_per_share: float
    current_price: float | None = None
    market_value: float | None = None
    day_change_amount: float | None = None
    day_change_percent: float | None = None
    total_gain_dollars: float | None = None
    total_gain_percent: float | None = None
