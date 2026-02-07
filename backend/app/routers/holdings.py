from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter
from app.schemas.holding import HoldingResponse
from app.services import holding_service

router = APIRouter()


@router.get("/{portfolio_id}/holdings", response_model=list[HoldingResponse])
def get_holdings(portfolio_id: UUID):
    return holding_service.get_holdings(portfolio_id)
