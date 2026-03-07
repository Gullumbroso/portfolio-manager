"""Live AI integration tests — real Anthropic API, mocked tool execution.

Run with: pytest -m live
Requires: ANTHROPIC_API_KEY env var set to a real key (or in backend/.env).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest

# Load .env before checking for API key
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from app.services.ai.ai_engine import stream_chat
from app.services.ai.tools import TOOL_DEFINITIONS


pytestmark = pytest.mark.live

FAKE_PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000001")

# Skip all tests if no real API key
_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not _api_key or _api_key == "test-key":
    pytestmark = [pytest.mark.live, pytest.mark.skip(reason="No real ANTHROPIC_API_KEY set")]


# ---------------------------------------------------------------------------
# Fixture data returned by mocked tool handlers
# ---------------------------------------------------------------------------

MOCK_QUOTE = {
    "ticker": "AAPL", "price": 185.50, "change_percent": 1.2,
    "company_name": "Apple Inc.", "market_cap": 2800000000000,
}
MOCK_QUOTE_MSFT = {
    "ticker": "MSFT", "price": 420.30, "change_percent": -0.3,
    "company_name": "Microsoft Corp.", "market_cap": 3100000000000,
}
MOCK_HOLDINGS = {
    "holdings": [
        {"ticker": "AAPL", "total_shares": 10, "avg_cost_per_share": 150},
        {"ticker": "MSFT", "total_shares": 5, "avg_cost_per_share": 380},
    ],
    "count": 2,
}
MOCK_SUMMARY = {
    "total_value": 50000, "market_value": 40000,
    "cash_balance": 10000, "total_deposits": 45000,
    "profit_dollars": 5000, "profit_percent": 11.1,
}
MOCK_NEWS = {
    "ticker": "TSLA", "article_count": 3,
    "articles": [
        {"headline": "Tesla Q4 earnings beat", "source": "Reuters"},
        {"headline": "Tesla opens new factory", "source": "Bloomberg"},
        {"headline": "Tesla stock rises", "source": "CNBC"},
    ],
}
MOCK_EXPIRATIONS = {
    "ticker": "NVDA", "expirations": ["2026-04-17", "2026-05-15", "2026-06-19"],
}
MOCK_CHAIN = {
    "ticker": "AAPL", "spot_price": 185.50, "expiry_date": "2026-04-17",
    "calls": [
        {"strike": 180, "lastPrice": 8.0, "bid": 7.8, "ask": 8.2, "impliedVolatility": 0.28, "openInterest": 5000, "volume": 1200},
        {"strike": 185, "lastPrice": 5.0, "bid": 4.8, "ask": 5.2, "impliedVolatility": 0.26, "openInterest": 8000, "volume": 2500},
        {"strike": 190, "lastPrice": 2.5, "bid": 2.3, "ask": 2.7, "impliedVolatility": 0.27, "openInterest": 6000, "volume": 1800},
    ],
    "puts": [
        {"strike": 180, "lastPrice": 2.5, "bid": 2.3, "ask": 2.7, "impliedVolatility": 0.29, "openInterest": 4000, "volume": 900},
        {"strike": 185, "lastPrice": 5.5, "bid": 5.3, "ask": 5.7, "impliedVolatility": 0.27, "openInterest": 7000, "volume": 2100},
        {"strike": 190, "lastPrice": 8.0, "bid": 7.8, "ask": 8.2, "impliedVolatility": 0.28, "openInterest": 5000, "volume": 1500},
    ],
}
MOCK_STRATEGY = {
    "ticker": "AAPL", "strategy_type": "long_call", "strategy_name": "Long Call",
    "confidence_score": 70, "risk_score": 3,
    "max_profit": 5000, "max_loss": -500, "breakeven_prices": [190.5],
    "capital_required": 500, "margin_requirement": 0, "risk_reward_ratio": 10.0,
    "has_unlimited_risk": False, "has_assignment_risk": False,
    "has_high_gamma": False, "has_volatility_sensitivity": False,
    "spot_price_at_analysis": 185.50, "expiration_date": "2026-04-17",
    "days_to_expiry": 41,
    "legs": [{"leg_order": 1, "action": "buy", "option_type": "call", "strike": 185,
              "contracts": 1, "premium": 5.0, "delta": 0.52, "gamma": 0.03,
              "theta": -0.05, "vega": 0.12}],
}


def _dispatch_mock(tool_name, tool_input, portfolio_id):
    """Mock dispatch that returns realistic fixture data based on tool name."""
    dispatch_map = {
        "get_stock_quote": lambda: MOCK_QUOTE if tool_input.get("ticker", "").upper() == "AAPL" else MOCK_QUOTE_MSFT,
        "get_stock_news": lambda: MOCK_NEWS,
        "get_portfolio_holdings": lambda: MOCK_HOLDINGS,
        "get_portfolio_summary": lambda: MOCK_SUMMARY,
        "get_options_expirations": lambda: MOCK_EXPIRATIONS,
        "get_options_chain": lambda: MOCK_CHAIN,
        "get_stock_history": lambda: {"ticker": tool_input.get("ticker", "?"), "data_points": 60, "price_change": 10.5, "price_change_pct": 5.8},
        "generate_options_strategy": lambda: MOCK_STRATEGY,
    }
    handler = dispatch_map.get(tool_name, lambda: {"error": f"Unknown: {tool_name}"})
    return handler()


def _collect_events(portfolio_id, messages):
    """Run stream_chat with mocked dispatch, collect all events and tool calls."""
    with patch("app.services.ai.ai_engine.dispatch_tool", side_effect=_dispatch_mock), \
         patch("app.services.ai.ai_engine.get_holdings", return_value=MOCK_HOLDINGS["holdings"]), \
         patch("app.services.ai.ai_engine.get_portfolio_summary", return_value=MOCK_SUMMARY):

        events = list(stream_chat(portfolio_id, messages))

    tool_calls = [e["data"]["tool"] for e in events if e["event"] == "tool_start"]
    return events, tool_calls


# ---------------------------------------------------------------------------
# 10.1  Stock Tool Selection
# ---------------------------------------------------------------------------

class TestStockToolSelection:
    def test_stock_quote(self):
        """'What's AAPL trading at?' should call get_stock_quote."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "What's AAPL trading at?"}],
        )
        assert "get_stock_quote" in tools

    def test_portfolio_question(self):
        """'How's my portfolio?' should call get_portfolio_holdings or get_portfolio_summary."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "How's my portfolio doing overall?"}],
        )
        assert "get_portfolio_holdings" in tools or "get_portfolio_summary" in tools

    def test_news_lookup(self):
        """'Any news on Tesla?' should call get_stock_news."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Any recent news on Tesla?"}],
        )
        assert "get_stock_news" in tools

    def test_multi_stock_compare(self):
        """'Compare AAPL and MSFT' should call get_stock_quote multiple times."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Compare AAPL and MSFT stock prices for me."}],
        )
        assert tools.count("get_stock_quote") >= 2


# ---------------------------------------------------------------------------
# 10.2  Options Tool Selection
# ---------------------------------------------------------------------------

class TestOptionsToolSelection:
    def test_expirations_query(self):
        """Asking for available dates should call get_options_expirations."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "What expiration dates are available for NVDA options?"}],
        )
        assert "get_options_expirations" in tools

    def test_options_chain_query(self):
        """Asking for an options chain should call get_options_chain."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Show me the options chain for AAPL expiring 2026-04-17"}],
        )
        assert "get_options_chain" in tools or "get_options_expirations" in tools

    def test_simple_call_strategy(self):
        """Asking for a simple bullish strategy should call generate_options_strategy."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "I'm very bullish on TSLA. Give me a simple long call option recommendation. Use expiry 2026-04-17."}],
        )
        assert "generate_options_strategy" in tools

    def test_iron_condor_strategy(self):
        """Asking for an iron condor should call generate_options_strategy."""
        _, tools = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Set up an iron condor on SPY expiring 2026-04-17. Use strikes 440/445/460/465."}],
        )
        assert "generate_options_strategy" in tools


# ---------------------------------------------------------------------------
# 10.3  Options Pipeline Verification
# ---------------------------------------------------------------------------

class TestOptionsPipelineVerification:
    def test_recommendation_event_emitted(self):
        """Strategy request should emit a recommendation SSE event."""
        events, _ = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Recommend a long call on AAPL expiring 2026-04-17, strike 185."}],
        )
        rec_events = [e for e in events if e["event"] == "recommendation"]
        assert len(rec_events) >= 1

    def test_recommendation_has_greeks(self):
        """Recommendation should contain server-computed Greeks."""
        events, _ = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Recommend a long call on AAPL expiring 2026-04-17, strike 185."}],
        )
        rec_events = [e for e in events if e["event"] == "recommendation"]
        if rec_events:
            rec = rec_events[0]["data"]["recommendation"]
            assert "legs" in rec
            if rec["legs"]:
                leg = rec["legs"][0]
                assert "delta" in leg
                assert "gamma" in leg

    def test_recommendation_has_risk_metrics(self):
        """Recommendation should contain server-computed risk metrics."""
        events, _ = _collect_events(
            FAKE_PORTFOLIO_ID,
            [{"role": "user", "content": "Recommend a long call on AAPL expiring 2026-04-17, strike 185."}],
        )
        rec_events = [e for e in events if e["event"] == "recommendation"]
        if rec_events:
            rec = rec_events[0]["data"]["recommendation"]
            assert "risk_score" in rec
            assert "max_profit" in rec
            assert "max_loss" in rec
