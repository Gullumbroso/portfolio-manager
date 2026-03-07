"""Tests for chat service DB operations (mocked Supabase)."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest


FAKE_PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000001")
FAKE_SESSION_ID = UUID("00000000-0000-0000-0000-000000000002")
FAKE_MESSAGE_ID = UUID("00000000-0000-0000-0000-000000000003")
FAKE_REC_ID = UUID("00000000-0000-0000-0000-000000000004")


def _chainable_db(execute_results):
    """Create a mock Supabase client where all .table() chains resolve to shared execute results.

    execute_results: list of MagicMock(data=[...]) — consumed in order across all execute() calls.
    """
    db = MagicMock()
    chain = MagicMock()
    # All chainable methods return the same chain object
    for method in ("select", "insert", "update", "delete", "eq", "order", "limit"):
        getattr(chain, method).return_value = chain
    chain.execute.side_effect = execute_results
    db.table.return_value = chain
    return db, chain


class TestChatServiceCreateSession:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_create_session(self, mock_get_db):
        db, chain = _chainable_db([
            MagicMock(data=[{
                "id": str(FAKE_SESSION_ID),
                "portfolio_id": str(FAKE_PORTFOLIO_ID),
                "title": None,
                "status": "active",
            }]),
        ])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import create_session
        result = create_session(FAKE_PORTFOLIO_ID, None)
        assert result["id"] == str(FAKE_SESSION_ID)
        db.table.assert_any_call("chat_sessions")


class TestChatServiceListSessions:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_list_sessions(self, mock_get_db):
        db, chain = _chainable_db([
            # First execute: list sessions
            MagicMock(data=[{
                "id": str(FAKE_SESSION_ID),
                "portfolio_id": str(FAKE_PORTFOLIO_ID),
                "title": "Test Session",
            }]),
            # Second execute: last message preview for session
            MagicMock(data=[{"content": "What's AAPL at?", "role": "user"}]),
        ])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import list_sessions
        result = list_sessions(FAKE_PORTFOLIO_ID)
        assert len(result) == 1
        assert result[0]["last_message_preview"] == "What's AAPL at?"


class TestChatServiceGetSession:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_get_session_not_found(self, mock_get_db):
        db, chain = _chainable_db([MagicMock(data=[])])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import get_session
        result = get_session(FAKE_SESSION_ID)
        assert result is None

    @patch("app.services.ai.chat_service.get_supabase")
    def test_get_session_with_messages(self, mock_get_db):
        db, chain = _chainable_db([
            # Session query
            MagicMock(data=[{
                "id": str(FAKE_SESSION_ID),
                "portfolio_id": str(FAKE_PORTFOLIO_ID),
                "title": "Test",
            }]),
            # Messages query
            MagicMock(data=[{
                "id": str(FAKE_MESSAGE_ID),
                "role": "user",
                "content": "Hello",
                "has_recommendation": False,
            }]),
        ])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import get_session
        result = get_session(FAKE_SESSION_ID)
        assert result is not None
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "Hello"


class TestChatServiceAddMessage:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_add_message(self, mock_get_db):
        db, chain = _chainable_db([
            # Insert message
            MagicMock(data=[{
                "id": str(FAKE_MESSAGE_ID),
                "session_id": str(FAKE_SESSION_ID),
                "role": "user",
                "content": "Hello",
            }]),
            # Touch session updated_at
            MagicMock(data=[{}]),
        ])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import add_message
        result = add_message(FAKE_SESSION_ID, "user", "Hello")
        assert result["role"] == "user"
        # 2 table calls: chat_messages insert + chat_sessions update
        assert db.table.call_count == 2


class TestChatServiceUpdateTitle:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_update_title(self, mock_get_db):
        db, chain = _chainable_db([MagicMock(data=[{}])])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import update_title
        update_title(FAKE_SESSION_ID, "New Title")
        db.table.assert_any_call("chat_sessions")


class TestChatServiceStoreRecommendation:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_store_recommendation_with_legs(self, mock_get_db):
        db, chain = _chainable_db([
            # Insert recommendation
            MagicMock(data=[{"id": str(FAKE_REC_ID)}]),
            # Insert leg 1
            MagicMock(data=[{}]),
            # Insert leg 2
            MagicMock(data=[{}]),
        ])
        mock_get_db.return_value = db

        recommendation = {
            "ticker": "AAPL", "strategy_type": "bull_call_spread",
            "strategy_name": "Bull Call Spread", "confidence_score": 75,
            "strategy_reasoning": "Bullish", "strike_reasoning": "ATM",
            "expiration_reasoning": "30 DTE", "entry_conditions": "Hold above 148",
            "exit_conditions": "50% profit", "adverse_scenario": "Below 140",
            "max_profit": 700, "max_loss": -300, "breakeven_prices": [103.0],
            "capital_required": 300, "margin_requirement": 0,
            "risk_reward_ratio": 2.33, "risk_score": 4,
            "has_unlimited_risk": False, "has_assignment_risk": False,
            "has_high_gamma": False, "has_volatility_sensitivity": False,
            "spot_price_at_analysis": 150.0, "expiration_date": "2026-04-17",
            "days_to_expiry": 30,
            "legs": [
                {"leg_order": 1, "action": "buy", "option_type": "call", "strike": 150,
                 "contracts": 1, "premium": 5.0, "bid": 4.8, "ask": 5.2,
                 "implied_volatility": 0.28, "open_interest": 5000, "volume": 1000,
                 "delta": 0.52, "gamma": 0.03, "theta": -0.05, "vega": 0.12},
                {"leg_order": 2, "action": "sell", "option_type": "call", "strike": 155,
                 "contracts": 1, "premium": 2.5, "bid": 2.3, "ask": 2.7,
                 "implied_volatility": 0.29, "open_interest": 3000, "volume": 600,
                 "delta": 0.35, "gamma": 0.025, "theta": -0.04, "vega": 0.10},
            ],
        }

        from app.services.ai.chat_service import store_recommendation
        result = store_recommendation(FAKE_MESSAGE_ID, str(FAKE_SESSION_ID), recommendation)
        assert result["id"] == str(FAKE_REC_ID)
        # 1 rec + 2 legs = 3 table calls
        assert db.table.call_count == 3
        db.table.assert_any_call("options_recommendations")
        db.table.assert_any_call("options_recommendation_legs")

    @patch("app.services.ai.chat_service.get_supabase")
    def test_store_recommendation_all_fields_mapped(self, mock_get_db):
        """Verify all recommendation fields are passed to the DB insert."""
        db, chain = _chainable_db([MagicMock(data=[{"id": str(FAKE_REC_ID)}])])
        mock_get_db.return_value = db

        recommendation = {
            "ticker": "AAPL", "strategy_type": "long_call", "strategy_name": "Test",
            "confidence_score": 80, "strategy_reasoning": "r1", "strike_reasoning": "r2",
            "expiration_reasoning": "r3", "entry_conditions": "e1", "exit_conditions": "e2",
            "adverse_scenario": "a1", "max_profit": 1000, "max_loss": -500,
            "breakeven_prices": [105], "capital_required": 500, "margin_requirement": 0,
            "risk_reward_ratio": 2.0, "risk_score": 3, "has_unlimited_risk": False,
            "has_assignment_risk": False, "has_high_gamma": False,
            "has_volatility_sensitivity": True, "spot_price_at_analysis": 150,
            "expiration_date": "2026-04-17", "days_to_expiry": 30, "legs": [],
        }

        from app.services.ai.chat_service import store_recommendation
        store_recommendation(FAKE_MESSAGE_ID, str(FAKE_SESSION_ID), recommendation)

        # First insert call is for the recommendation
        rec_data = chain.insert.call_args_list[0][0][0]
        assert rec_data["ticker"] == "AAPL"
        assert rec_data["confidence_score"] == 80
        assert rec_data["has_volatility_sensitivity"] is True
        assert rec_data["max_profit"] == 1000
        assert rec_data["risk_score"] == 3


class TestChatServiceRecordDecision:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_record_decision(self, mock_get_db):
        db, chain = _chainable_db([
            MagicMock(data=[{
                "id": "decision-1",
                "recommendation_id": str(FAKE_REC_ID),
                "decision": "accepted",
                "notes": "Looks good",
            }]),
        ])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import record_decision
        result = record_decision(FAKE_REC_ID, "accepted", "Looks good")
        assert result["decision"] == "accepted"
        assert result["notes"] == "Looks good"


class TestChatServiceDeleteSession:
    @patch("app.services.ai.chat_service.get_supabase")
    def test_delete_session(self, mock_get_db):
        db, chain = _chainable_db([MagicMock(data=[{"id": str(FAKE_SESSION_ID)}])])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import delete_session
        result = delete_session(FAKE_SESSION_ID)
        assert result is True

    @patch("app.services.ai.chat_service.get_supabase")
    def test_delete_session_not_found(self, mock_get_db):
        db, chain = _chainable_db([MagicMock(data=[])])
        mock_get_db.return_value = db

        from app.services.ai.chat_service import delete_session
        result = delete_session(FAKE_SESSION_ID)
        assert result is False
