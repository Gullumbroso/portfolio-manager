from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class PortfolioCreate(BaseModel):
    name: str
    description: str = ""


class PortfolioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PortfolioResponse(BaseModel):
    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class PortfolioSummary(BaseModel):
    id: UUID
    name: str
    total_value: float
    market_value: float
    cash_balance: float
    total_deposits: float
    profit_dollars: float
    profit_percent: float


class PortfolioPerformancePoint(BaseModel):
    date: str
    total_value: float
    cash_balance: float
    market_value: float
    total_deposits: float
    profit: float
