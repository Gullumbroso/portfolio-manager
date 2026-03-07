"""Tests for AI engine: system prompt, streaming, title generation."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock, PropertyMock
from uuid import UUID

import pytest

from app.services.ai.ai_engine import _build_system_prompt, stream_chat, generate_session_title


FAKE_PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# 5.1  _build_system_prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    @patch("app.services.ai.ai_engine.get_portfolio_summary")
    @patch("app.services.ai.ai_engine.get_holdings")
    def test_with_holdings(self, mock_holdings, mock_summary):
        mock_holdings.return_value = [
            {"ticker": "AAPL", "total_shares": 10, "avg_cost_per_share": 150.0,
             "current_price": 185.0, "total_gain_dollars": 350.0, "total_gain_percent": 23.3},
        ]
        mock_summary.return_value = {
            "cash_balance": 5000, "total_value": 50000,
            "profit_dollars": 3500, "profit_percent": 7.5,
        }

        prompt = _build_system_prompt(FAKE_PORTFOLIO_ID)
        assert "AAPL" in prompt
        assert "10 shares" in prompt
        assert "$185.00" in prompt
        assert "$5,000.00" in prompt
        assert "$50,000.00" in prompt

    @patch("app.services.ai.ai_engine.get_portfolio_summary")
    @patch("app.services.ai.ai_engine.get_holdings")
    def test_empty_portfolio(self, mock_holdings, mock_summary):
        mock_holdings.return_value = []
        mock_summary.return_value = {
            "cash_balance": 0, "total_value": 0,
            "profit_dollars": 0, "profit_percent": 0,
        }

        prompt = _build_system_prompt(FAKE_PORTFOLIO_ID)
        assert "No holdings yet." in prompt

    @patch("app.services.ai.ai_engine.get_portfolio_summary")
    @patch("app.services.ai.ai_engine.get_holdings")
    def test_holdings_fetch_fails_gracefully(self, mock_holdings, mock_summary):
        mock_holdings.side_effect = Exception("DB down")
        mock_summary.side_effect = Exception("DB down")

        prompt = _build_system_prompt(FAKE_PORTFOLIO_ID)
        assert "No holdings yet." in prompt
        assert "$0.00" in prompt

    @patch("app.services.ai.ai_engine.get_portfolio_summary")
    @patch("app.services.ai.ai_engine.get_holdings")
    def test_contains_cash_and_value(self, mock_holdings, mock_summary):
        mock_holdings.return_value = []
        mock_summary.return_value = {
            "cash_balance": 12345.67, "total_value": 12345.67,
            "profit_dollars": 0, "profit_percent": 0,
        }
        prompt = _build_system_prompt(FAKE_PORTFOLIO_ID)
        assert "$12,345.67" in prompt


# ---------------------------------------------------------------------------
# 5.2  stream_chat  (mocked Anthropic client)
# ---------------------------------------------------------------------------

def _make_stream_events(text_chunks, tool_calls=None):
    """Build a sequence of mock stream events.

    text_chunks: list of strings (text deltas)
    tool_calls: list of dicts with {id, name, input_json}
    """
    events = []
    # Tool use blocks first
    if tool_calls:
        for tc in tool_calls:
            start_event = MagicMock()
            start_event.type = "content_block_start"
            start_event.content_block.type = "tool_use"
            start_event.content_block.id = tc["id"]
            start_event.content_block.name = tc["name"]
            events.append(start_event)

            delta_event = MagicMock()
            delta_event.type = "content_block_delta"
            delta_event.delta.type = "input_json_delta"
            delta_event.delta.partial_json = json.dumps(tc.get("input", {}))
            events.append(delta_event)

    # Text blocks
    for chunk in text_chunks:
        delta = MagicMock()
        delta.type = "content_block_delta"
        delta.delta.type = "text_delta"
        delta.delta.text = chunk
        events.append(delta)

    return events


def _mock_stream_context(events, stop_reason="end_turn"):
    """Create a mock context manager for client.messages.stream()."""
    stream = MagicMock()
    stream.__iter__ = MagicMock(return_value=iter(events))
    final_msg = MagicMock()
    final_msg.stop_reason = stop_reason
    stream.get_final_message.return_value = final_msg
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=stream)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


class TestStreamChat:
    @patch("app.services.ai.ai_engine._build_system_prompt", return_value="System prompt")
    @patch("app.services.ai.ai_engine._get_client")
    def test_text_only_response(self, mock_get_client, mock_prompt):
        client = MagicMock()
        mock_get_client.return_value = client

        events = _make_stream_events(["Hello", " world"])
        client.messages.stream.return_value = _mock_stream_context(events)

        results = list(stream_chat(FAKE_PORTFOLIO_ID, [{"role": "user", "content": "hi"}]))

        text_events = [e for e in results if e["event"] == "text"]
        assert len(text_events) == 2
        assert text_events[0]["data"]["content"] == "Hello"
        assert text_events[1]["data"]["content"] == " world"

    @patch("app.services.ai.ai_engine.dispatch_tool")
    @patch("app.services.ai.ai_engine._build_system_prompt", return_value="System prompt")
    @patch("app.services.ai.ai_engine._get_client")
    def test_single_tool_call(self, mock_get_client, mock_prompt, mock_dispatch):
        client = MagicMock()
        mock_get_client.return_value = client

        # First call: tool use
        tool_events = _make_stream_events(
            [],
            tool_calls=[{"id": "tool_1", "name": "get_stock_quote", "input": {"ticker": "AAPL"}}],
        )
        tool_ctx = _mock_stream_context(tool_events, stop_reason="tool_use")

        # Second call: text response after tool
        text_events = _make_stream_events(["AAPL is at $185"])
        text_ctx = _mock_stream_context(text_events, stop_reason="end_turn")

        client.messages.stream.side_effect = [tool_ctx, text_ctx]
        mock_dispatch.return_value = {"ticker": "AAPL", "price": 185}

        results = list(stream_chat(FAKE_PORTFOLIO_ID, [{"role": "user", "content": "AAPL price?"}]))

        event_types = [e["event"] for e in results]
        assert "tool_start" in event_types
        assert "tool_result" in event_types
        assert "text" in event_types

    @patch("app.services.ai.ai_engine.dispatch_tool")
    @patch("app.services.ai.ai_engine._build_system_prompt", return_value="System prompt")
    @patch("app.services.ai.ai_engine._get_client")
    def test_recommendation_emitted(self, mock_get_client, mock_prompt, mock_dispatch):
        client = MagicMock()
        mock_get_client.return_value = client

        # Tool call: generate_options_strategy
        tool_events = _make_stream_events(
            [],
            tool_calls=[{"id": "tool_1", "name": "generate_options_strategy", "input": {"ticker": "AAPL"}}],
        )
        tool_ctx = _mock_stream_context(tool_events, stop_reason="tool_use")

        text_events = _make_stream_events(["Here's your strategy"])
        text_ctx = _mock_stream_context(text_events, stop_reason="end_turn")

        client.messages.stream.side_effect = [tool_ctx, text_ctx]
        mock_dispatch.return_value = {
            "ticker": "AAPL", "strategy_name": "Bull Call",
            "risk_score": 4, "legs": [],
        }

        results = list(stream_chat(FAKE_PORTFOLIO_ID, [{"role": "user", "content": "strategy"}]))

        rec_events = [e for e in results if e["event"] == "recommendation"]
        assert len(rec_events) == 1
        assert rec_events[0]["data"]["recommendation"]["strategy_name"] == "Bull Call"

    @patch("app.services.ai.ai_engine.dispatch_tool")
    @patch("app.services.ai.ai_engine._build_system_prompt", return_value="System prompt")
    @patch("app.services.ai.ai_engine._get_client")
    def test_tool_error_in_result(self, mock_get_client, mock_prompt, mock_dispatch):
        """Tool returning an error should still emit tool_result with error summary."""
        client = MagicMock()
        mock_get_client.return_value = client

        tool_events = _make_stream_events(
            [],
            tool_calls=[{"id": "tool_1", "name": "get_stock_quote", "input": {"ticker": "BAD"}}],
        )
        tool_ctx = _mock_stream_context(tool_events, stop_reason="tool_use")
        text_events = _make_stream_events(["Sorry, couldn't find that."])
        text_ctx = _mock_stream_context(text_events, stop_reason="end_turn")

        client.messages.stream.side_effect = [tool_ctx, text_ctx]
        mock_dispatch.return_value = {"error": "Not found"}

        results = list(stream_chat(FAKE_PORTFOLIO_ID, [{"role": "user", "content": "BAD price"}]))

        tool_results = [e for e in results if e["event"] == "tool_result"]
        assert len(tool_results) == 1
        assert "Error" in tool_results[0]["data"]["summary"]


# ---------------------------------------------------------------------------
# 5.3  generate_session_title
# ---------------------------------------------------------------------------

class TestGenerateSessionTitle:
    @patch("app.services.ai.ai_engine._get_client")
    def test_returns_short_title(self, mock_get_client):
        client = MagicMock()
        mock_get_client.return_value = client

        response = MagicMock()
        response.content = [MagicMock(text='"AAPL Options Strategy"')]
        client.messages.create.return_value = response

        title = generate_session_title([
            {"role": "user", "content": "Give me an options strategy for AAPL"},
            {"role": "assistant", "content": "Here's a bull call spread..."},
        ])

        assert title == "AAPL Options Strategy"
        # Verify it strips quotes
        assert '"' not in title
