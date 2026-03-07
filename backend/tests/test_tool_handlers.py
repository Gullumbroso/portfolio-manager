"""Tests for AI tool handlers and dispatch."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest

from app.services.ai.tools import (
    handle_get_stock_quote,
    handle_get_stock_history,
    handle_get_stock_news,
    handle_get_portfolio_holdings,
    handle_get_portfolio_summary,
    handle_get_options_expirations,
    handle_get_options_chain,
    handle_generate_options_strategy,
    dispatch_tool,
)

FAKE_PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# 4.1  Stock Tools
# ---------------------------------------------------------------------------

class TestStockToolHandlers:
    @patch("app.services.ai.tools.get_quote")
    def test_stock_quote_success(self, mock_quote):
        mock_quote.return_value = {"ticker": "AAPL", "price": 185.5, "change_percent": 1.2}
        result = handle_get_stock_quote("aapl")
        mock_quote.assert_called_with("AAPL")
        assert result["price"] == 185.5

    @patch("app.services.ai.tools.get_quote")
    def test_stock_quote_invalid_ticker(self, mock_quote):
        mock_quote.side_effect = Exception("Not found")
        result = handle_get_stock_quote("ZZZZZZ")
        assert "error" in result

    @patch("app.services.ai.tools.get_history")
    def test_stock_history_success(self, mock_history):
        mock_history.return_value = [
            {"close": 180.0, "date": "2026-01-01"},
            {"close": 190.0, "date": "2026-03-01"},
        ]
        result = handle_get_stock_history("AAPL", "3M")
        assert result["data_points"] == 2
        assert result["price_change"] == 10.0
        assert result["price_change_pct"] == pytest.approx(5.56, abs=0.1)

    @patch("app.services.ai.tools.get_history")
    def test_stock_history_empty(self, mock_history):
        mock_history.return_value = []
        result = handle_get_stock_history("AAPL")
        assert "error" in result

    @patch("app.services.ai.tools.get_news")
    def test_stock_news_has_articles(self, mock_news):
        mock_news.return_value = [{"headline": f"News {i}"} for i in range(15)]
        result = handle_get_stock_news("AAPL")
        assert result["article_count"] == 15
        assert len(result["articles"]) == 10  # capped at 10

    @patch("app.services.ai.tools.get_news")
    def test_stock_news_no_articles(self, mock_news):
        mock_news.return_value = []
        result = handle_get_stock_news("AAPL")
        assert result["articles"] == []
        assert "message" in result

    @patch("app.services.ai.tools.get_holdings")
    def test_portfolio_holdings_success(self, mock_holdings):
        mock_holdings.return_value = [{"ticker": "AAPL", "total_shares": 10}]
        result = handle_get_portfolio_holdings(portfolio_id=FAKE_PORTFOLIO_ID)
        assert result["count"] == 1

    @patch("app.services.ai.tools.get_holdings")
    def test_portfolio_holdings_empty(self, mock_holdings):
        mock_holdings.return_value = []
        result = handle_get_portfolio_holdings(portfolio_id=FAKE_PORTFOLIO_ID)
        assert result["holdings"] == []
        assert "message" in result

    @patch("app.services.ai.tools.get_portfolio_summary")
    def test_portfolio_summary(self, mock_summary):
        mock_summary.return_value = {"total_value": 50000, "cash_balance": 10000}
        result = handle_get_portfolio_summary(portfolio_id=FAKE_PORTFOLIO_ID)
        assert result["total_value"] == 50000


# ---------------------------------------------------------------------------
# 4.2  Options Tools
# ---------------------------------------------------------------------------

class TestOptionsToolHandlers:
    @patch("app.services.ai.tools.get_available_expirations")
    def test_expirations_success(self, mock_exp):
        mock_exp.return_value = ["2026-04-17", "2026-05-15"]
        result = handle_get_options_expirations("NVDA")
        assert result["ticker"] == "NVDA"
        assert len(result["expirations"]) == 2

    @patch("app.services.ai.tools.get_available_expirations")
    def test_expirations_no_options(self, mock_exp):
        mock_exp.return_value = []
        result = handle_get_options_expirations("PRIVATE")
        assert "error" in result

    @patch("app.services.ai.tools.get_chain_summary")
    def test_options_chain_success(self, mock_chain):
        mock_chain.return_value = {"ticker": "AAPL", "calls": [], "puts": []}
        result = handle_get_options_chain("AAPL", "2026-04-17")
        assert result["ticker"] == "AAPL"

    @patch("app.services.ai.tools.get_chain_summary")
    def test_options_chain_error(self, mock_chain):
        mock_chain.side_effect = Exception("No chain")
        result = handle_get_options_chain("AAPL", "2026-04-17")
        assert "error" in result


# ---------------------------------------------------------------------------
# 4.3  generate_options_strategy — Full Pipeline
# ---------------------------------------------------------------------------

def _mock_chain_data(spot=150):
    """Return mock chain summary with calls and puts around spot price."""
    return {
        "ticker": "AAPL",
        "spot_price": spot,
        "expiry_date": "2026-04-17",
        "calls": [
            {"strike": 145, "lastPrice": 8.0, "bid": 7.8, "ask": 8.2, "impliedVolatility": 0.30, "openInterest": 2000, "volume": 500},
            {"strike": 150, "lastPrice": 5.0, "bid": 4.8, "ask": 5.2, "impliedVolatility": 0.28, "openInterest": 5000, "volume": 1000},
            {"strike": 155, "lastPrice": 2.5, "bid": 2.3, "ask": 2.7, "impliedVolatility": 0.29, "openInterest": 3000, "volume": 600},
            {"strike": 160, "lastPrice": 1.0, "bid": 0.8, "ask": 1.2, "impliedVolatility": 0.31, "openInterest": 1000, "volume": 200},
        ],
        "puts": [
            {"strike": 140, "lastPrice": 1.5, "bid": 1.3, "ask": 1.7, "impliedVolatility": 0.32, "openInterest": 1500, "volume": 300},
            {"strike": 145, "lastPrice": 3.0, "bid": 2.8, "ask": 3.2, "impliedVolatility": 0.30, "openInterest": 2500, "volume": 450},
            {"strike": 150, "lastPrice": 5.5, "bid": 5.3, "ask": 5.7, "impliedVolatility": 0.28, "openInterest": 4000, "volume": 800},
            {"strike": 155, "lastPrice": 8.5, "bid": 8.3, "ask": 8.7, "impliedVolatility": 0.29, "openInterest": 2000, "volume": 400},
        ],
    }


class TestGenerateOptionsStrategy:
    """Test the full generate_options_strategy pipeline."""

    def _future_date(self, days=30):
        return (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_long_call_enriched_with_greeks(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Long AAPL Call",
            expiry_date=self._future_date(30),
            legs=[{"action": "buy", "option_type": "call", "strike": 155}],
        )

        assert "error" not in result
        assert len(result["legs"]) == 1
        leg = result["legs"][0]
        # Greeks computed server-side (not AI-provided)
        assert "delta" in leg and leg["delta"] > 0
        assert "gamma" in leg and leg["gamma"] > 0
        assert "theta" in leg and leg["theta"] < 0
        assert "vega" in leg and leg["vega"] > 0
        # Premium from chain data
        assert leg["premium"] == 2.5
        assert leg["bid"] == 2.3
        assert leg["ask"] == 2.7

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_bull_call_spread_risk_metrics(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="bull_call_spread",
            strategy_name="Bull Call Spread",
            expiry_date=self._future_date(30),
            legs=[
                {"action": "buy", "option_type": "call", "strike": 150},
                {"action": "sell", "option_type": "call", "strike": 155},
            ],
        )

        assert "error" not in result
        assert result["max_profit"] is not None
        assert result["max_loss"] is not None and result["max_loss"] < 0
        assert result["risk_reward_ratio"] is not None
        assert result["capital_required"] is not None
        assert result["risk_score"] >= 1
        assert isinstance(result["breakeven_prices"], list)

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_iron_condor_four_legs(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="iron_condor",
            strategy_name="Iron Condor",
            expiry_date=self._future_date(30),
            legs=[
                {"action": "sell", "option_type": "put", "strike": 145},
                {"action": "buy", "option_type": "put", "strike": 140},
                {"action": "sell", "option_type": "call", "strike": 155},
                {"action": "buy", "option_type": "call", "strike": 160},
            ],
        )

        assert len(result["legs"]) == 4
        assert result["risk_score"] is not None
        # All legs should have Greeks
        for leg in result["legs"]:
            assert "delta" in leg
            assert "gamma" in leg

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_naked_call_unlimited_risk_flagged(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="naked_call",
            strategy_name="Naked Call",
            expiry_date=self._future_date(30),
            legs=[{"action": "sell", "option_type": "call", "strike": 155}],
        )

        assert result["has_unlimited_risk"] is True
        assert result["risk_score"] >= 8

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_near_expiry_high_gamma(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Near Expiry Call",
            expiry_date=self._future_date(3),
            legs=[{"action": "buy", "option_type": "call", "strike": 150}],
        )

        assert result["has_high_gamma"] is True
        assert result["days_to_expiry"] <= 7

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_expired_date_rejected(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Expired",
            expiry_date="2020-01-01",
            legs=[{"action": "buy", "option_type": "call", "strike": 150}],
        )

        assert "error" in result
        assert "past" in result["error"]

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_invalid_date_format(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Bad Date",
            expiry_date="not-a-date",
            legs=[{"action": "buy", "option_type": "call", "strike": 150}],
        )

        assert "error" in result
        assert "Invalid date" in result["error"]

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_chain_unavailable_falls_back(self, mock_quote, mock_chain):
        """When chain data is unavailable, should fall back to default IV."""
        mock_quote.return_value = {"price": 150.0}
        mock_chain.side_effect = Exception("yfinance down")

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Fallback",
            expiry_date=self._future_date(30),
            legs=[{"action": "buy", "option_type": "call", "strike": 155}],
        )

        assert "error" not in result
        # Still has Greeks (computed with default IV=0.3)
        assert result["legs"][0]["delta"] > 0
        assert result["legs"][0]["implied_volatility"] == 0.3

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_margin_computed(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="naked_call",
            strategy_name="Naked Call",
            expiry_date=self._future_date(30),
            legs=[{"action": "sell", "option_type": "call", "strike": 155}],
        )

        assert result["margin_requirement"] > 0

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_spot_price_captured(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 152.75}
        mock_chain.return_value = _mock_chain_data(152.75)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Test",
            expiry_date=self._future_date(30),
            legs=[{"action": "buy", "option_type": "call", "strike": 155}],
        )

        assert result["spot_price_at_analysis"] == 152.75

    @patch("app.services.ai.tools.get_chain_summary")
    @patch("app.services.ai.tools.get_quote")
    def test_reasoning_fields_passed_through(self, mock_quote, mock_chain):
        mock_quote.return_value = {"price": 150.0}
        mock_chain.return_value = _mock_chain_data(150)

        result = handle_generate_options_strategy(
            ticker="AAPL",
            strategy_type="long_call",
            strategy_name="Test",
            expiry_date=self._future_date(30),
            legs=[{"action": "buy", "option_type": "call", "strike": 155}],
            confidence_score=75,
            strategy_reasoning="Bullish on AAPL",
            strike_reasoning="Near ATM for good delta",
            expiration_reasoning="30 DTE for theta balance",
            entry_conditions="Enter if price holds above 148",
            exit_conditions="Exit at 50% profit",
            adverse_scenario="Stock drops below 140",
        )

        assert result["confidence_score"] == 75
        assert result["strategy_reasoning"] == "Bullish on AAPL"
        assert result["strike_reasoning"] == "Near ATM for good delta"
        assert result["expiration_reasoning"] == "30 DTE for theta balance"
        assert result["entry_conditions"] == "Enter if price holds above 148"
        assert result["exit_conditions"] == "Exit at 50% profit"
        assert result["adverse_scenario"] == "Stock drops below 140"


# ---------------------------------------------------------------------------
# 4.4  dispatch_tool
# ---------------------------------------------------------------------------

class TestDispatchTool:
    @patch("app.services.ai.tools.get_quote")
    def test_known_tool_dispatches(self, mock_quote):
        mock_quote.return_value = {"ticker": "AAPL", "price": 150}
        result = dispatch_tool("get_stock_quote", {"ticker": "AAPL"}, FAKE_PORTFOLIO_ID)
        assert result["price"] == 150

    def test_unknown_tool(self):
        result = dispatch_tool("nonexistent_tool", {}, FAKE_PORTFOLIO_ID)
        assert "error" in result
        assert "Unknown tool" in result["error"]

    @patch("app.services.ai.tools.get_holdings")
    def test_portfolio_id_injected(self, mock_holdings):
        mock_holdings.return_value = [{"ticker": "AAPL"}]
        dispatch_tool("get_portfolio_holdings", {}, FAKE_PORTFOLIO_ID)
        mock_holdings.assert_called_once_with(FAKE_PORTFOLIO_ID)
