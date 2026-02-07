from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services import transaction_service

router = APIRouter()


@router.get("/{portfolio_id}/transactions", response_model=list[TransactionResponse])
def list_transactions(portfolio_id: UUID, limit: int = 50, offset: int = 0):
    return transaction_service.list_transactions(portfolio_id, limit, offset)


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(portfolio_id: UUID, data: TransactionCreate):
    return transaction_service.create_transaction(portfolio_id, data)


@router.delete("/{portfolio_id}/transactions/{transaction_id}", status_code=204)
def delete_transaction(portfolio_id: UUID, transaction_id: UUID):
    transaction_service.delete_transaction(portfolio_id, transaction_id)
