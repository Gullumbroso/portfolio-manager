from __future__ import annotations
from fastapi import APIRouter, Query
from app.schemas.market import QuoteResponse, HistoryPoint, NewsArticle
from app.services import market_data_service

router = APIRouter()


@router.get("/quote/{ticker}", response_model=QuoteResponse)
def get_quote(ticker: str):
    quote = market_data_service.get_quote(ticker.upper())
    return quote


@router.get("/history/{ticker}", response_model=list[HistoryPoint])
def get_history(ticker: str, period: str = "1M"):
    return market_data_service.get_history(ticker.upper(), period)


@router.get("/news/{ticker}", response_model=list[NewsArticle])
def get_news(ticker: str):
    return market_data_service.get_news(ticker.upper())


@router.get("/batch-quotes", response_model=dict[str, QuoteResponse])
def get_batch_quotes(tickers: str = Query(..., description="Comma-separated tickers")):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    return market_data_service.get_batch_quotes(ticker_list)
