"""Black-Scholes pricing, Greeks computation, and strategy risk analysis."""
from __future__ import annotations
import math

RISK_FREE_RATE = 0.05  # 5% annual

# Pure-Python normal distribution (replaces scipy.stats.norm)
_SQRT_2PI = math.sqrt(2 * math.pi)


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / _SQRT_2PI


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))


def black_scholes_price(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str
) -> float:
    """Compute Black-Scholes option price.

    S: spot price, K: strike, T: time to expiry (years),
    r: risk-free rate, sigma: implied volatility, option_type: 'call' or 'put'
    """
    if T <= 0 or sigma <= 0:
        # At expiry, return intrinsic value
        if option_type == "call":
            return max(S - K, 0)
        return max(K - S, 0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "call":
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def compute_greeks(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str
) -> dict:
    """Compute option Greeks: delta, gamma, theta (per day), vega (per 1% vol)."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
        delta = 1.0 if (option_type == "call" and S > K) else (-1.0 if (option_type == "put" and S < K) else 0.0)
        return {"delta": delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T

    gamma = _norm_pdf(d1) / (S * sigma * sqrt_T)
    vega = S * _norm_pdf(d1) * sqrt_T / 100  # per 1% vol move

    if option_type == "call":
        delta = _norm_cdf(d1)
        theta = (
            -S * _norm_pdf(d1) * sigma / (2 * sqrt_T)
            - r * K * math.exp(-r * T) * _norm_cdf(d2)
        ) / 365
    else:
        delta = _norm_cdf(d1) - 1
        theta = (
            -S * _norm_pdf(d1) * sigma / (2 * sqrt_T)
            + r * K * math.exp(-r * T) * _norm_cdf(-d2)
        ) / 365

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 4),
        "theta": round(theta, 4),
        "vega": round(vega, 4),
    }


def compute_strategy_risk(legs: list[dict], spot_price: float) -> dict:
    """Compute max profit, max loss, breakevens, and risk/reward for a multi-leg strategy.

    Each leg: {action, option_type, strike, contracts, premium}
    """
    if not legs:
        return {}

    # Build P&L at expiry across a range of prices
    strikes = [leg["strike"] for leg in legs]
    min_price = min(strikes) * 0.5
    max_price = max(strikes) * 1.5
    step = (max_price - min_price) / 1000

    prices = [min_price + i * step for i in range(1001)]
    pnl_values = []

    for price in prices:
        pnl = 0
        for leg in legs:
            strike = leg["strike"]
            premium = leg.get("premium", 0) or 0
            contracts = leg.get("contracts", 1)
            multiplier = 100 * contracts

            if leg["option_type"] == "call":
                intrinsic = max(price - strike, 0)
            else:
                intrinsic = max(strike - price, 0)

            if leg["action"] == "buy":
                pnl += (intrinsic - premium) * multiplier
            else:
                pnl += (premium - intrinsic) * multiplier

        pnl_values.append(pnl)

    max_profit = max(pnl_values)
    max_loss = min(pnl_values)

    # Check for effectively unlimited profit/loss (> 10x capital)
    total_premium = sum(
        abs(leg.get("premium", 0) or 0) * (leg.get("contracts", 1)) * 100
        for leg in legs
    )
    if total_premium > 0:
        if max_profit > total_premium * 50:
            max_profit = float("inf")
        if abs(max_loss) > total_premium * 50:
            max_loss = float("-inf")

    # Find breakeven points (where P&L crosses zero)
    breakevens = []
    for i in range(len(pnl_values) - 1):
        if pnl_values[i] * pnl_values[i + 1] < 0:
            # Linear interpolation
            p1, p2 = prices[i], prices[i + 1]
            v1, v2 = pnl_values[i], pnl_values[i + 1]
            be = p1 + (p2 - p1) * abs(v1) / (abs(v1) + abs(v2))
            breakevens.append(round(be, 2))

    risk_reward = None
    if max_loss != 0 and max_loss != float("-inf") and max_profit != float("inf"):
        risk_reward = round(abs(max_profit / max_loss), 2)

    return {
        "max_profit": round(max_profit, 2) if max_profit != float("inf") else None,
        "max_loss": round(max_loss, 2) if max_loss != float("-inf") else None,
        "breakeven_prices": breakevens,
        "risk_reward_ratio": risk_reward,
        "capital_required": round(total_premium, 2),
    }


def compute_margin_requirement(legs: list[dict], spot_price: float) -> float:
    """Estimate margin requirement for a strategy."""
    margin = 0
    for leg in legs:
        if leg["action"] == "sell":
            strike = leg["strike"]
            premium = leg.get("premium", 0) or 0
            contracts = leg.get("contracts", 1)
            multiplier = 100 * contracts

            if leg["option_type"] == "call":
                # Naked call: max(20% of underlying - OTM amount + premium, 10% of underlying + premium)
                otm = max(strike - spot_price, 0)
                margin += max(
                    0.20 * spot_price * multiplier - otm * multiplier + premium * multiplier,
                    0.10 * spot_price * multiplier + premium * multiplier,
                )
            else:
                # Naked put: max(20% of underlying - OTM amount + premium, 10% of strike + premium)
                otm = max(spot_price - strike, 0)
                margin += max(
                    0.20 * spot_price * multiplier - otm * multiplier + premium * multiplier,
                    0.10 * strike * multiplier + premium * multiplier,
                )

    # If there are offsetting long legs (spreads), reduce margin
    has_long = any(leg["action"] == "buy" for leg in legs)
    has_short = any(leg["action"] == "sell" for leg in legs)
    if has_long and has_short:
        # For spreads, margin is limited to max loss
        risk = compute_strategy_risk(legs, spot_price)
        if risk.get("max_loss") is not None:
            margin = min(margin, abs(risk["max_loss"]))

    return round(margin, 2)
