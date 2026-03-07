"""Tests for Black-Scholes pricing, Greeks, strategy risk, and margin computation."""
from __future__ import annotations

import math
import pytest

from app.services.options.quant_engine import (
    black_scholes_price,
    compute_greeks,
    compute_strategy_risk,
    compute_margin_requirement,
    RISK_FREE_RATE,
)


# ---------------------------------------------------------------------------
# 1.1  black_scholes_price
# ---------------------------------------------------------------------------

class TestBlackScholesPrice:
    def test_atm_call_known_value(self):
        """ATM call: S=100, K=100, T=0.25, sigma=0.3 should be ~6.33."""
        price = black_scholes_price(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert abs(price - 6.33) < 0.5  # within $0.50 of known BS value

    def test_deep_itm_put(self):
        """Deep ITM put should be close to discounted intrinsic."""
        price = black_scholes_price(80, 100, 0.25, RISK_FREE_RATE, 0.3, "put")
        intrinsic = 100 - 80
        assert price >= intrinsic * 0.9  # at least 90% of intrinsic
        assert price < intrinsic + 5  # not wildly above intrinsic

    def test_at_expiry_itm_call(self):
        price = black_scholes_price(110, 100, 0, RISK_FREE_RATE, 0.3, "call")
        assert price == 10.0

    def test_at_expiry_otm_call(self):
        price = black_scholes_price(90, 100, 0, RISK_FREE_RATE, 0.3, "call")
        assert price == 0.0

    def test_at_expiry_itm_put(self):
        price = black_scholes_price(90, 100, 0, RISK_FREE_RATE, 0.3, "put")
        assert price == 10.0

    def test_at_expiry_otm_put(self):
        price = black_scholes_price(110, 100, 0, RISK_FREE_RATE, 0.3, "put")
        assert price == 0.0

    def test_zero_iv(self):
        """Zero IV should return intrinsic value."""
        price = black_scholes_price(110, 100, 0.25, RISK_FREE_RATE, 0, "call")
        assert price == 10.0

    def test_put_call_parity(self):
        """C - P = S - K*e^(-rT)"""
        S, K, T, sigma = 100, 100, 0.25, 0.3
        call = black_scholes_price(S, K, T, RISK_FREE_RATE, sigma, "call")
        put = black_scholes_price(S, K, T, RISK_FREE_RATE, sigma, "put")
        expected_diff = S - K * math.exp(-RISK_FREE_RATE * T)
        assert abs((call - put) - expected_diff) < 0.01

    def test_call_price_positive(self):
        price = black_scholes_price(100, 100, 0.5, RISK_FREE_RATE, 0.25, "call")
        assert price > 0

    def test_higher_vol_higher_price(self):
        low_vol = black_scholes_price(100, 100, 0.25, RISK_FREE_RATE, 0.2, "call")
        high_vol = black_scholes_price(100, 100, 0.25, RISK_FREE_RATE, 0.5, "call")
        assert high_vol > low_vol


# ---------------------------------------------------------------------------
# 1.2  compute_greeks
# ---------------------------------------------------------------------------

class TestComputeGreeks:
    def test_atm_call_delta(self):
        g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert 0.50 < g["delta"] < 0.65

    def test_atm_put_delta(self):
        g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "put")
        assert -0.35 > g["delta"] > -0.55

    def test_gamma_positive(self):
        g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert g["gamma"] > 0

    def test_call_theta_negative(self):
        g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert g["theta"] < 0

    def test_vega_positive(self):
        g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert g["vega"] > 0

    def test_deep_itm_call_delta_near_one(self):
        g = compute_greeks(200, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert g["delta"] > 0.95

    def test_deep_otm_call_delta_near_zero(self):
        g = compute_greeks(50, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert g["delta"] < 0.05

    def test_at_expiry_itm_call(self):
        g = compute_greeks(110, 100, 0, RISK_FREE_RATE, 0.3, "call")
        assert g["delta"] == 1.0
        assert g["gamma"] == 0.0
        assert g["theta"] == 0.0
        assert g["vega"] == 0.0

    def test_at_expiry_otm_call(self):
        g = compute_greeks(90, 100, 0, RISK_FREE_RATE, 0.3, "call")
        assert g["delta"] == 0.0

    def test_at_expiry_itm_put(self):
        g = compute_greeks(90, 100, 0, RISK_FREE_RATE, 0.3, "put")
        assert g["delta"] == -1.0

    def test_at_expiry_otm_put(self):
        g = compute_greeks(110, 100, 0, RISK_FREE_RATE, 0.3, "put")
        assert g["delta"] == 0.0

    def test_near_expiry_high_gamma(self):
        """Near expiry ATM gamma should be much larger than far-dated."""
        near = compute_greeks(100, 100, 1 / 365, RISK_FREE_RATE, 0.3, "call")
        far = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        assert near["gamma"] > far["gamma"] * 3

    def test_put_call_delta_relationship(self):
        """call delta - put delta = 1 (approximately, for same strike)."""
        call_g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        put_g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "put")
        assert abs((call_g["delta"] - put_g["delta"]) - 1.0) < 0.01

    def test_greeks_are_rounded(self):
        g = compute_greeks(100, 100, 0.25, RISK_FREE_RATE, 0.3, "call")
        for key in ("delta", "gamma", "theta", "vega"):
            # Check that values have at most 4 decimal places
            assert round(g[key], 4) == g[key]


# ---------------------------------------------------------------------------
# 1.3  compute_strategy_risk
# ---------------------------------------------------------------------------

class TestComputeStrategyRisk:
    def test_long_call(self):
        # Use non-round premium to avoid exact-zero P&L on grid points
        legs = [{"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5.3}]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_loss"] == -530  # 5.3 * 100
        assert risk["max_profit"] > 0  # profit capped by analysis range
        assert len(risk["breakeven_prices"]) == 1
        assert abs(risk["breakeven_prices"][0] - 105.3) < 1

    def test_long_put(self):
        legs = [{"action": "buy", "option_type": "put", "strike": 100, "contracts": 1, "premium": 3.2}]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_loss"] == pytest.approx(-320, abs=5)
        assert len(risk["breakeven_prices"]) == 1
        assert abs(risk["breakeven_prices"][0] - 96.8) < 1

    def test_bull_call_spread(self):
        legs = [
            {"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5},
            {"action": "sell", "option_type": "call", "strike": 110, "contracts": 1, "premium": 2},
        ]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_loss"] == pytest.approx(-300, abs=50)  # net debit ~$3 * 100
        assert risk["max_profit"] == pytest.approx(700, abs=50)  # spread width - debit
        assert len(risk["breakeven_prices"]) == 1
        assert abs(risk["breakeven_prices"][0] - 103) < 2

    def test_bear_put_spread(self):
        legs = [
            {"action": "buy", "option_type": "put", "strike": 110, "contracts": 1, "premium": 6},
            {"action": "sell", "option_type": "put", "strike": 100, "contracts": 1, "premium": 2},
        ]
        risk = compute_strategy_risk(legs, 105)
        assert risk["max_loss"] == pytest.approx(-400, abs=50)
        assert risk["max_profit"] == pytest.approx(600, abs=50)

    def test_iron_condor(self):
        legs = [
            {"action": "sell", "option_type": "put", "strike": 90, "contracts": 1, "premium": 2.1},
            {"action": "buy", "option_type": "put", "strike": 85, "contracts": 1, "premium": 0.8},
            {"action": "sell", "option_type": "call", "strike": 110, "contracts": 1, "premium": 2.1},
            {"action": "buy", "option_type": "call", "strike": 115, "contracts": 1, "premium": 0.8},
        ]
        risk = compute_strategy_risk(legs, 100)
        # Max profit = net credit * 100
        assert risk["max_profit"] is not None and risk["max_profit"] > 0
        # Max loss is capped (spread width - credit)
        assert risk["max_loss"] is not None and risk["max_loss"] < 0
        # Should have breakevens on both sides
        assert len(risk["breakeven_prices"]) >= 1

    def test_naked_call_large_loss(self):
        """Naked call has large downside. Unlimited detection depends on range vs threshold."""
        legs = [{"action": "sell", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5}]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_profit"] == 500  # premium collected
        assert risk["max_loss"] < -2000  # significant loss within analysis range

    def test_straddle(self):
        # Premiums sum to 10.13 to avoid exact-zero on grid points
        legs = [
            {"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5.43},
            {"action": "buy", "option_type": "put", "strike": 100, "contracts": 1, "premium": 4.7},
        ]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_loss"] == pytest.approx(-1013, abs=50)
        assert len(risk["breakeven_prices"]) == 2
        breakevens = sorted(risk["breakeven_prices"])
        assert abs(breakevens[0] - 89.87) < 2
        assert abs(breakevens[1] - 110.13) < 2

    def test_empty_legs(self):
        assert compute_strategy_risk([], 100) == {}

    def test_multi_contract(self):
        legs = [{"action": "buy", "option_type": "call", "strike": 100, "contracts": 3, "premium": 5}]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_loss"] == -1500  # 5 * 100 * 3
        assert risk["capital_required"] == 1500

    def test_risk_reward_ratio(self):
        """Bull call spread should have a computable risk/reward ratio."""
        legs = [
            {"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5},
            {"action": "sell", "option_type": "call", "strike": 110, "contracts": 1, "premium": 2},
        ]
        risk = compute_strategy_risk(legs, 100)
        assert risk["risk_reward_ratio"] is not None
        assert risk["risk_reward_ratio"] > 0

    def test_naked_call_poor_risk_reward(self):
        """Naked call has much more downside than upside."""
        legs = [{"action": "sell", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5}]
        risk = compute_strategy_risk(legs, 100)
        assert risk["risk_reward_ratio"] is not None
        assert risk["risk_reward_ratio"] < 0.5  # reward much less than risk

    def test_capital_required_is_total_premium(self):
        legs = [
            {"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5},
            {"action": "sell", "option_type": "call", "strike": 110, "contracts": 1, "premium": 2},
        ]
        risk = compute_strategy_risk(legs, 100)
        assert risk["capital_required"] == 700  # (5 + 2) * 100

    def test_missing_premium_defaults_to_zero(self):
        legs = [{"action": "buy", "option_type": "call", "strike": 100, "contracts": 1}]
        risk = compute_strategy_risk(legs, 100)
        assert risk["max_loss"] == 0  # no premium paid


# ---------------------------------------------------------------------------
# 1.4  compute_margin_requirement
# ---------------------------------------------------------------------------

class TestComputeMarginRequirement:
    def test_long_only_no_margin(self):
        legs = [{"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5}]
        assert compute_margin_requirement(legs, 100) == 0

    def test_naked_call_margin(self):
        legs = [{"action": "sell", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5}]
        margin = compute_margin_requirement(legs, 100)
        # max(20%*100*100 - 0 + 500, 10%*100*100 + 500) = max(2500, 1500) = 2500
        assert margin == 2500

    def test_naked_put_margin(self):
        legs = [{"action": "sell", "option_type": "put", "strike": 100, "contracts": 1, "premium": 3}]
        margin = compute_margin_requirement(legs, 100)
        # max(20%*100*100 - 0 + 300, 10%*100*100 + 300) = max(2300, 1300) = 2300
        assert margin == 2300

    def test_spread_margin_reduced_to_max_loss(self):
        legs = [
            {"action": "buy", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5},
            {"action": "sell", "option_type": "call", "strike": 110, "contracts": 1, "premium": 2},
        ]
        margin = compute_margin_requirement(legs, 100)
        risk = compute_strategy_risk(legs, 100)
        # Margin should be min(naked margin, |max_loss|)
        assert margin <= abs(risk["max_loss"]) + 1  # allow rounding

    def test_otm_naked_call_lower_margin(self):
        """OTM naked call should have lower margin due to OTM offset."""
        atm = compute_margin_requirement(
            [{"action": "sell", "option_type": "call", "strike": 100, "contracts": 1, "premium": 5}], 100
        )
        otm = compute_margin_requirement(
            [{"action": "sell", "option_type": "call", "strike": 120, "contracts": 1, "premium": 2}], 100
        )
        assert otm < atm
