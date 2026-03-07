from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date


# --- Sessions ---

class SessionCreate(BaseModel):
    title: str | None = None


class SessionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    last_message_preview: str | None = None


class SessionDetailResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []


# --- Messages ---

class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    has_recommendation: bool = False
    created_at: datetime
    recommendations: list[RecommendationResponse] = []


# --- Recommendations ---

class RecommendationLegResponse(BaseModel):
    id: UUID
    leg_order: int
    action: str
    option_type: str
    strike: float
    contracts: int
    premium: float | None = None
    bid: float | None = None
    ask: float | None = None
    implied_volatility: float | None = None
    open_interest: int | None = None
    volume: int | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None


class RecommendationResponse(BaseModel):
    id: UUID
    message_id: UUID
    session_id: UUID
    ticker: str
    strategy_type: str
    strategy_name: str
    confidence_score: float | None = None
    strategy_reasoning: str | None = None
    strike_reasoning: str | None = None
    expiration_reasoning: str | None = None
    entry_conditions: str | None = None
    exit_conditions: str | None = None
    adverse_scenario: str | None = None
    max_profit: float | None = None
    max_loss: float | None = None
    breakeven_prices: list[float] = []
    capital_required: float | None = None
    margin_requirement: float | None = None
    risk_reward_ratio: float | None = None
    risk_score: int | None = None
    has_unlimited_risk: bool = False
    has_assignment_risk: bool = False
    has_high_gamma: bool = False
    has_volatility_sensitivity: bool = False
    spot_price_at_analysis: float | None = None
    expiration_date: date | None = None
    days_to_expiry: int | None = None
    legs: list[RecommendationLegResponse] = []
    decision: DecisionResponse | None = None
    created_at: datetime


# --- Decisions ---

class DecisionCreate(BaseModel):
    decision: str
    notes: str = ""


class DecisionResponse(BaseModel):
    id: UUID
    recommendation_id: UUID
    decision: str
    notes: str
    created_at: datetime


# Forward refs
SessionDetailResponse.model_rebuild()
MessageResponse.model_rebuild()
