"""Tests for options data service (yfinance integration layer)."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
import math

import pandas as pd
import pytest

from app.services.options.options_data_service import (
    get_available_expirations,
    get_options_chain,
    get_chain_summary,
)


def _make_options_df(strikes, last_prices, bids, asks, volumes, ois, ivs, itms):
    """Helper to build a DataFrame that mimics yfinance option_chain output."""
    return pd.DataFrame({
        "strike": strikes,
        "lastPrice": last_prices,
        "bid": bids,
        "ask": asks,
        "volume": volumes,
        "openInterest": ois,
        "impliedVolatility": ivs,
        "inTheMoney": itms,
    })


@pytest.fixture
def mock_ticker():
    """Create a mock yfinance Ticker."""
    ticker = MagicMock()
    ticker.options = ("2026-04-17", "2026-05-15", "2026-06-19")

    calls_df = _make_options_df(
        strikes=[140, 145, 150, 155, 160],
        last_prices=[12.5, 8.3, 5.1, 2.8, 1.2],
        bids=[12.0, 8.0, 4.9, 2.6, 1.0],
        asks=[13.0, 8.6, 5.3, 3.0, 1.4],
        volumes=[100, 200, 500, 300, 50],
        ois=[1000, 2000, 5000, 3000, 500],
        ivs=[0.32, 0.30, 0.28, 0.29, 0.31],
        itms=[True, True, True, False, False],
    )
    puts_df = _make_options_df(
        strikes=[140, 145, 150, 155, 160],
        last_prices=[1.1, 2.3, 4.0, 6.8, 10.2],
        bids=[0.9, 2.1, 3.8, 6.5, 9.8],
        asks=[1.3, 2.5, 4.2, 7.1, 10.6],
        volumes=[80, 150, 400, 250, 40],
        ois=[800, 1500, 4000, 2500, 400],
        ivs=[0.33, 0.31, 0.29, 0.30, 0.32],
        itms=[False, False, False, True, True],
    )

    chain = MagicMock()
    chain.calls = calls_df
    chain.puts = puts_df
    ticker.option_chain.return_value = chain
    return ticker


class TestGetAvailableExpirations:
    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_valid_ticker(self, mock_yf_ticker, mock_ticker):
        mock_yf_ticker.return_value = mock_ticker
        result = get_available_expirations("AAPL")
        assert result == ["2026-04-17", "2026-05-15", "2026-06-19"]

    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_invalid_ticker_returns_empty(self, mock_yf_ticker):
        ticker = MagicMock()
        ticker.options = property(lambda self: (_ for _ in ()).throw(Exception("No options")))
        # Simulate .options raising
        type(ticker).options = property(lambda self: (_ for _ in ()).throw(Exception("No options")))
        mock_yf_ticker.return_value = ticker
        result = get_available_expirations("INVALID")
        assert result == []


class TestGetOptionsChain:
    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_parses_dataframe(self, mock_yf_ticker, mock_ticker):
        mock_yf_ticker.return_value = mock_ticker
        result = get_options_chain("AAPL", "2026-04-17")

        assert result["expiry_date"] == "2026-04-17"
        assert len(result["calls"]) == 5
        assert len(result["puts"]) == 5

        # Check first call has correct fields
        call = result["calls"][0]
        assert call["strike"] == 140
        assert call["lastPrice"] == 12.5
        assert call["bid"] == 12.0
        assert call["ask"] == 13.0
        assert call["volume"] == 100
        assert call["openInterest"] == 1000
        assert abs(call["impliedVolatility"] - 0.32) < 0.01
        assert call["inTheMoney"] is True

    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_handles_nan_volume_and_oi(self, mock_yf_ticker):
        """NaN values in volume/OI should become 0."""
        ticker = MagicMock()
        calls_df = _make_options_df(
            strikes=[100],
            last_prices=[5.0],
            bids=[4.8],
            asks=[5.2],
            volumes=[float("nan")],
            ois=[float("nan")],
            ivs=[0.3],
            itms=[True],
        )
        puts_df = _make_options_df(
            strikes=[100],
            last_prices=[3.0],
            bids=[2.8],
            asks=[3.2],
            volumes=[0],
            ois=[0],
            ivs=[0.3],
            itms=[False],
        )
        chain = MagicMock()
        chain.calls = calls_df
        chain.puts = puts_df
        ticker.option_chain.return_value = chain
        mock_yf_ticker.return_value = ticker

        result = get_options_chain("TEST", "2026-04-17")
        assert result["calls"][0]["volume"] == 0
        assert result["calls"][0]["openInterest"] == 0


class TestGetChainSummary:
    @patch("app.services.market_data_service.get_quote")
    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_atm_filtering(self, mock_yf_ticker, mock_get_quote, mock_ticker):
        """Should return strikes nearest to ATM."""
        mock_yf_ticker.return_value = mock_ticker
        mock_get_quote.return_value = {"price": 150.0}

        result = get_chain_summary("AAPL", "2026-04-17", num_strikes=2)
        # num_strikes=2 → returns 4 nearest strikes (2*2)
        assert len(result["calls"]) == 4
        assert len(result["puts"]) == 4
        assert result["spot_price"] == 150.0
        assert result["ticker"] == "AAPL"

        # Nearest strikes to 150 should include 145, 150, 155, (and 140 or 160)
        call_strikes = [c["strike"] for c in result["calls"]]
        assert 150 in call_strikes

    @patch("app.services.market_data_service.get_quote")
    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_spot_between_strikes(self, mock_yf_ticker, mock_get_quote, mock_ticker):
        """When spot is between strikes, nearest on both sides included."""
        mock_yf_ticker.return_value = mock_ticker
        mock_get_quote.return_value = {"price": 152.5}

        result = get_chain_summary("AAPL", "2026-04-17", num_strikes=2)
        call_strikes = [c["strike"] for c in result["calls"]]
        # 150 and 155 are nearest to 152.5
        assert 150 in call_strikes
        assert 155 in call_strikes

    @patch("app.services.market_data_service.get_quote")
    @patch("app.services.options.options_data_service.yf.Ticker")
    def test_few_strikes_returns_all(self, mock_yf_ticker, mock_get_quote, mock_ticker):
        """When fewer strikes than num_strikes*2, return all."""
        mock_yf_ticker.return_value = mock_ticker
        mock_get_quote.return_value = {"price": 150.0}

        result = get_chain_summary("AAPL", "2026-04-17", num_strikes=10)
        # Only 5 strikes available, all should be returned
        assert len(result["calls"]) == 5
        assert len(result["puts"]) == 5
