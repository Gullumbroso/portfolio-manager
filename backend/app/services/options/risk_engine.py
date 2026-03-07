"""Risk assessment for options strategies."""
from __future__ import annotations


STRATEGY_RISK_BASE = {
    "long_call": 3,
    "long_put": 3,
    "covered_call": 4,
    "cash_secured_put": 5,
    "bull_call_spread": 4,
    "bear_put_spread": 4,
    "bull_put_spread": 5,
    "bear_call_spread": 5,
    "iron_condor": 5,
    "iron_butterfly": 5,
    "straddle": 6,
    "strangle": 6,
    "naked_call": 9,
    "naked_put": 8,
    "calendar_spread": 5,
    "diagonal_spread": 5,
}


def assess_risk(
    strategy_type: str,
    legs: list[dict],
    spot_price: float,
    days_to_expiry: int,
) -> dict:
    """Compute risk score (1-10) and flag conditions."""
    base_score = STRATEGY_RISK_BASE.get(strategy_type, 5)

    has_unlimited_risk = _check_unlimited_risk(strategy_type, legs)
    has_assignment_risk = _check_assignment_risk(legs, spot_price)
    has_high_gamma = days_to_expiry <= 7
    has_volatility_sensitivity = _check_vol_sensitivity(legs)

    # Adjust score
    score = base_score
    if has_unlimited_risk:
        score = max(score, 8)
    if has_high_gamma:
        score += 1
    if has_assignment_risk:
        score += 1
    score = min(score, 10)

    return {
        "risk_score": score,
        "has_unlimited_risk": has_unlimited_risk,
        "has_assignment_risk": has_assignment_risk,
        "has_high_gamma": has_high_gamma,
        "has_volatility_sensitivity": has_volatility_sensitivity,
    }


def _check_unlimited_risk(strategy_type: str, legs: list[dict]) -> bool:
    """Check if strategy has unlimited risk (naked short calls, etc.)."""
    if strategy_type in ("naked_call",):
        return True

    short_calls = [l for l in legs if l["action"] == "sell" and l["option_type"] == "call"]
    long_calls = [l for l in legs if l["action"] == "buy" and l["option_type"] == "call"]

    if short_calls and not long_calls:
        return True

    return False


def _check_assignment_risk(legs: list[dict], spot_price: float) -> bool:
    """Check if any short legs are ITM (assignment risk)."""
    for leg in legs:
        if leg["action"] != "sell":
            continue
        strike = leg["strike"]
        if leg["option_type"] == "call" and spot_price > strike:
            return True
        if leg["option_type"] == "put" and spot_price < strike:
            return True
    return False


def _check_vol_sensitivity(legs: list[dict]) -> bool:
    """Check if strategy is significantly sensitive to volatility changes."""
    total_vega = 0
    for leg in legs:
        vega = abs(leg.get("vega", 0) or 0)
        if leg["action"] == "sell":
            total_vega -= vega
        else:
            total_vega += vega
    return abs(total_vega) > 0.5
