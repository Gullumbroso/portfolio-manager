from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioSummary,
    PortfolioPerformancePoint,
)
from app.services import portfolio_service, holding_service

router = APIRouter()


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios():
    return portfolio_service.list_portfolios()


@router.post("", response_model=PortfolioResponse, status_code=201)
def create_portfolio(data: PortfolioCreate):
    try:
        return portfolio_service.create_portfolio(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: UUID):
    try:
        return portfolio_service.get_portfolio(portfolio_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Portfolio not found")


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: UUID, data: PortfolioUpdate):
    try:
        return portfolio_service.update_portfolio(portfolio_id, data)
    except Exception:
        raise HTTPException(status_code=404, detail="Portfolio not found")


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: UUID):
    portfolio_service.delete_portfolio(portfolio_id)


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummary)
def get_portfolio_summary(portfolio_id: UUID):
    try:
        portfolio = portfolio_service.get_portfolio(portfolio_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    summary = holding_service.get_portfolio_summary(portfolio_id)
    return {
        "id": portfolio["id"],
        "name": portfolio["name"],
        **summary,
    }


@router.get("/{portfolio_id}/performance", response_model=list[PortfolioPerformancePoint])
def get_portfolio_performance(portfolio_id: UUID, period: str = "1M"):
    return portfolio_service.get_performance(portfolio_id, period)
