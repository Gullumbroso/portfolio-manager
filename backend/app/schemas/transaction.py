from __future__ import annotations
from pydantic import BaseModel, model_validator
from datetime import datetime
from uuid import UUID
from enum import Enum


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransactionCreate(BaseModel):
    type: TransactionType
    ticker: str | None = None
    shares: float | None = None
    price_per_share: float | None = None
    amount: float | None = None
    note: str = ""
    transacted_at: datetime | None = None
    # For BUY: amount to auto-deposit as external funding (0 = use existing cash only)
    auto_fund_amount: float = 0.0

    @model_validator(mode="after")
    def validate_transaction(self):
        if self.type in (TransactionType.BUY, TransactionType.SELL):
            if not self.ticker:
                raise ValueError("ticker is required for BUY/SELL transactions")
            if not self.shares or self.shares <= 0:
                raise ValueError("shares must be positive for BUY/SELL transactions")
            if not self.price_per_share or self.price_per_share <= 0:
                raise ValueError("price_per_share must be positive for BUY/SELL transactions")
            self.ticker = self.ticker.upper()
            self.amount = round(self.shares * self.price_per_share, 2)
        else:
            if not self.amount or self.amount <= 0:
                raise ValueError("amount must be positive for DEPOSIT/WITHDRAWAL transactions")
            self.ticker = None
            self.shares = None
            self.price_per_share = None
        return self


class TransactionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    type: TransactionType
    ticker: str | None
    shares: float | None
    price_per_share: float | None
    amount: float
    note: str
    transacted_at: datetime
    created_at: datetime
