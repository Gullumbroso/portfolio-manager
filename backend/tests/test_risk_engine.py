"""Tests for risk assessment engine."""
from __future__ import annotations

import pytest

from app.services.options.risk_engine import assess_risk


def _leg(action="buy", option_type="call", strike=100, vega=0.1):
    return {"action": action, "option_type": option_type, "strike": strike, "vega": vega}


class TestAssessRisk:
    # --- Base scores ---

    def test_long_call_base_score(self):
        result = assess_risk("long_call", [_leg("buy", "call", 110)], spot_price=100, days_to_expiry=30)
        assert result["risk_score"] == 3
        assert not result["has_unlimited_risk"]
        assert not result["has_assignment_risk"]
        assert not result["has_high_gamma"]
        assert not result["has_volatility_sensitivity"]

    def test_naked_call_base_score(self):
        result = assess_risk("naked_call", [_leg("sell", "call", 100)], spot_price=90, days_to_expiry=30)
        assert result["risk_score"] >= 8
        assert result["has_unlimited_risk"]

    def test_naked_call_near_expiry(self):
        """Naked call + near expiry: base 9 → unlimited bumps to 8 (already 9) + 1 gamma = 10."""
        result = assess_risk("naked_call", [_leg("sell", "call", 110)], spot_price=100, days_to_expiry=5)
        assert result["risk_score"] == 10
        assert result["has_unlimited_risk"]
        assert result["has_high_gamma"]

    def test_bull_call_spread_base_score(self):
        legs = [_leg("buy", "call", 100), _leg("sell", "call", 110)]
        result = assess_risk("bull_call_spread", legs, spot_price=100, days_to_expiry=30)
        assert result["risk_score"] == 4

    def test_iron_condor_with_short_itm_and_near_expiry(self):
        """Iron condor base=5, short ITM call (+1 assignment), near expiry (+1 gamma) = 7."""
        legs = [
            _leg("sell", "put", 90),
            _leg("buy", "put", 85),
            _leg("sell", "call", 95),  # ITM: spot=100 > 95
            _leg("buy", "call", 105),
        ]
        result = assess_risk("iron_condor", legs, spot_price=100, days_to_expiry=5)
        assert result["risk_score"] == 7
        assert result["has_assignment_risk"]
        assert result["has_high_gamma"]

    # --- Unlimited risk detection ---

    def test_short_calls_without_long_calls_unlimited(self):
        """Short calls without offsetting long calls = unlimited risk, even if not labeled naked_call."""
        legs = [_leg("sell", "call", 100), _leg("buy", "put", 90)]
        result = assess_risk("custom", legs, spot_price=100, days_to_expiry=30)
        assert result["has_unlimited_risk"]

    # --- Assignment risk ---

    def test_short_itm_call_assignment(self):
        legs = [_leg("sell", "call", 95)]  # spot=100 > strike=95
        result = assess_risk("covered_call", legs, spot_price=100, days_to_expiry=30)
        assert result["has_assignment_risk"]

    def test_short_otm_call_no_assignment(self):
        legs = [_leg("sell", "call", 110)]  # spot=100 < strike=110
        result = assess_risk("covered_call", legs, spot_price=100, days_to_expiry=30)
        assert not result["has_assignment_risk"]

    def test_short_itm_put_assignment(self):
        legs = [_leg("sell", "put", 110)]  # spot=100 < strike=110
        result = assess_risk("cash_secured_put", legs, spot_price=100, days_to_expiry=30)
        assert result["has_assignment_risk"]

    # --- Volatility sensitivity ---

    def test_high_net_vega_sensitive(self):
        legs = [_leg("buy", "call", 100, vega=0.6)]
        result = assess_risk("long_call", legs, spot_price=100, days_to_expiry=30)
        assert result["has_volatility_sensitivity"]

    def test_low_net_vega_not_sensitive(self):
        legs = [_leg("buy", "call", 100, vega=0.3)]
        result = assess_risk("long_call", legs, spot_price=100, days_to_expiry=30)
        assert not result["has_volatility_sensitivity"]

    # --- Unknown strategy ---

    def test_unknown_strategy_defaults_to_5(self):
        result = assess_risk("unknown_strategy", [_leg()], spot_price=100, days_to_expiry=30)
        assert result["risk_score"] == 5

    # --- Score clamping ---

    def test_score_clamped_to_10(self):
        """Even with all adjustments, score should not exceed 10."""
        legs = [_leg("sell", "call", 90, vega=0.6)]  # ITM short call, no long
        result = assess_risk("naked_call", legs, spot_price=100, days_to_expiry=3)
        assert result["risk_score"] <= 10
