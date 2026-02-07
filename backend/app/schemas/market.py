from __future__ import annotations
from pydantic import BaseModel


class QuoteResponse(BaseModel):
    ticker: str
    price: float
    change_amount: float
    change_percent: float
    name: str | None = None


class HistoryPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class NewsArticle(BaseModel):
    headline: str
    summary: str
    source: str
    url: str
    image: str | None = None
    datetime: int
