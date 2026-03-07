"""Tool definitions for Claude and their handler implementations."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime, date

from app.services.market_data_service import get_quote, get_history, get_news
from app.services.holding_service import get_holdings, get_portfolio_summary
from app.services.options.options_data_service import (
    get_available_expirations,
    get_chain_summary,
)
from app.services.options.quant_engine import (
    compute_greeks,
    compute_strategy_risk,
    compute_margin_requirement,
    RISK_FREE_RATE,
)
from app.services.options.risk_engine import assess_risk


# --- Tool Schemas (what Claude sees) ---

TOOL_DEFINITIONS = [
    {
        "name": "get_stock_quote",
        "description": "Get current stock price, daily change, and basic info for a ticker symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, MSFT)"}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_stock_history",
        "description": "Get historical price data for a stock. Periods: 1D, 1W, 1M, 3M, 6M, YTD, 1Y, ALL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"},
                "period": {"type": "string", "description": "Time period", "enum": ["1D", "1W", "1M", "3M", "6M", "YTD", "1Y", "ALL"]},
            },
            "required": ["ticker", "period"],
        },
    },
    {
        "name": "get_stock_news",
        "description": "Get recent news articles for a stock ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_portfolio_holdings",
        "description": "Get current portfolio holdings with live prices, cost basis, and gains for each position.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_portfolio_summary",
        "description": "Get portfolio summary: total value, market value, cash balance, total deposits, profit.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_options_expirations",
        "description": "Get available options expiration dates for a ticker. Call this before get_options_chain to know which dates are available.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_options_chain",
        "description": "Get options chain data (calls and puts near ATM) for a ticker and expiration date. Includes strikes, premiums, IV, volume, and open interest.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"},
                "expiry_date": {"type": "string", "description": "Expiration date in YYYY-MM-DD format"},
            },
            "required": ["ticker", "expiry_date"],
        },
    },
    {
        "name": "generate_options_strategy",
        "description": "Generate a complete options strategy recommendation with computed Greeks, risk metrics, and analysis. Use this when you want to present a structured strategy card to the user. Provide the legs of the strategy you're recommending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"},
                "strategy_type": {
                    "type": "string",
                    "description": "Strategy type identifier",
                    "enum": [
                        "long_call", "long_put", "covered_call", "cash_secured_put",
                        "bull_call_spread", "bear_put_spread", "bull_put_spread", "bear_call_spread",
                        "iron_condor", "iron_butterfly", "straddle", "strangle",
                        "naked_call", "naked_put", "calendar_spread", "diagonal_spread",
                    ],
                },
                "strategy_name": {"type": "string", "description": "Human-readable strategy name"},
                "expiry_date": {"type": "string", "description": "Expiration date YYYY-MM-DD"},
                "confidence_score": {"type": "number", "description": "Confidence 0-100"},
                "legs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["buy", "sell"]},
                            "option_type": {"type": "string", "enum": ["call", "put"]},
                            "strike": {"type": "number"},
                            "contracts": {"type": "integer", "default": 1},
                        },
                        "required": ["action", "option_type", "strike"],
                    },
                },
                "strategy_reasoning": {"type": "string"},
                "strike_reasoning": {"type": "string"},
                "expiration_reasoning": {"type": "string"},
                "entry_conditions": {"type": "string"},
                "exit_conditions": {"type": "string"},
                "adverse_scenario": {"type": "string"},
            },
            "required": ["ticker", "strategy_type", "strategy_name", "expiry_date", "legs"],
        },
    },
]


# --- Tool Handlers ---

def handle_get_stock_quote(ticker: str, **_) -> dict:
    try:
        return get_quote(ticker.upper())
    except Exception as e:
        return {"error": f"Could not fetch quote for {ticker}: {str(e)}"}


def handle_get_stock_history(ticker: str, period: str = "1M", **_) -> dict:
    try:
        data = get_history(ticker.upper(), period)
        if not data:
            return {"error": f"No history data for {ticker}"}
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data_points": len(data),
            "latest": data[-1] if data else None,
            "earliest": data[0] if data else None,
            "price_change": round(data[-1]["close"] - data[0]["close"], 2) if len(data) >= 2 else 0,
            "price_change_pct": round((data[-1]["close"] - data[0]["close"]) / data[0]["close"] * 100, 2) if len(data) >= 2 and data[0]["close"] > 0 else 0,
        }
    except Exception as e:
        return {"error": f"Could not fetch history for {ticker}: {str(e)}"}


def handle_get_stock_news(ticker: str, **_) -> dict:
    articles = get_news(ticker.upper())
    if not articles:
        return {"ticker": ticker.upper(), "articles": [], "message": "No recent news found"}
    return {
        "ticker": ticker.upper(),
        "article_count": len(articles),
        "articles": articles[:10],
    }


def handle_get_portfolio_holdings(portfolio_id: UUID, **_) -> dict:
    holdings = get_holdings(portfolio_id)
    if not holdings:
        return {"holdings": [], "message": "No holdings in this portfolio"}
    return {"holdings": holdings, "count": len(holdings)}


def handle_get_portfolio_summary(portfolio_id: UUID, **_) -> dict:
    return get_portfolio_summary(portfolio_id)


def handle_get_options_expirations(ticker: str, **_) -> dict:
    expirations = get_available_expirations(ticker.upper())
    if not expirations:
        return {"error": f"No options available for {ticker}. This ticker may not have listed options."}
    return {"ticker": ticker.upper(), "expirations": expirations}


def handle_get_options_chain(ticker: str, expiry_date: str, **_) -> dict:
    try:
        return get_chain_summary(ticker.upper(), expiry_date)
    except Exception as e:
        return {"error": f"Could not fetch options chain for {ticker} exp {expiry_date}: {str(e)}"}


def handle_generate_options_strategy(
    ticker: str,
    strategy_type: str,
    strategy_name: str,
    expiry_date: str,
    legs: list[dict],
    confidence_score: float | None = None,
    strategy_reasoning: str | None = None,
    strike_reasoning: str | None = None,
    expiration_reasoning: str | None = None,
    entry_conditions: str | None = None,
    exit_conditions: str | None = None,
    adverse_scenario: str | None = None,
    **_,
) -> dict:
    """Full pipeline: fetch chain data, compute Greeks, risk metrics, return structured recommendation."""
    ticker = ticker.upper()

    try:
        quote = get_quote(ticker)
        spot_price = quote["price"]
    except Exception as e:
        return {"error": f"Could not fetch price for {ticker}: {str(e)}"}

    # Compute days to expiry
    try:
        exp_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        days_to_expiry = (exp_date - date.today()).days
        if days_to_expiry < 0:
            return {"error": f"Expiration date {expiry_date} is in the past"}
        T = days_to_expiry / 365.0
    except ValueError:
        return {"error": f"Invalid date format: {expiry_date}"}

    # Try to get chain data for premium/IV info
    try:
        chain = get_chain_summary(ticker, expiry_date)
        chain_calls = {opt["strike"]: opt for opt in chain.get("calls", [])}
        chain_puts = {opt["strike"]: opt for opt in chain.get("puts", [])}
    except Exception:
        chain_calls = {}
        chain_puts = {}

    # Enrich legs with market data and Greeks
    enriched_legs = []
    for i, leg in enumerate(legs):
        strike = leg["strike"]
        option_type = leg["option_type"]
        contracts = leg.get("contracts", 1)

        # Look up chain data
        chain_data = chain_calls.get(strike, {}) if option_type == "call" else chain_puts.get(strike, {})

        iv = chain_data.get("impliedVolatility", 0.3)
        premium = chain_data.get("lastPrice", 0)
        bid = chain_data.get("bid", 0)
        ask = chain_data.get("ask", 0)
        oi = chain_data.get("openInterest", 0)
        vol = chain_data.get("volume", 0)

        # Compute Greeks
        greeks = compute_greeks(spot_price, strike, T, RISK_FREE_RATE, iv, option_type)

        enriched_legs.append({
            "leg_order": i + 1,
            "action": leg["action"],
            "option_type": option_type,
            "strike": strike,
            "contracts": contracts,
            "premium": round(premium, 2),
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "implied_volatility": round(iv, 4),
            "open_interest": oi,
            "volume": vol,
            **greeks,
        })

    # Compute strategy-level risk
    risk_legs = [
        {"action": l["action"], "option_type": l["option_type"], "strike": l["strike"],
         "contracts": l["contracts"], "premium": l["premium"]}
        for l in enriched_legs
    ]
    risk_metrics = compute_strategy_risk(risk_legs, spot_price)
    margin = compute_margin_requirement(risk_legs, spot_price)
    risk_assessment = assess_risk(strategy_type, enriched_legs, spot_price, days_to_expiry)

    return {
        "ticker": ticker,
        "strategy_type": strategy_type,
        "strategy_name": strategy_name,
        "confidence_score": confidence_score,
        "strategy_reasoning": strategy_reasoning,
        "strike_reasoning": strike_reasoning,
        "expiration_reasoning": expiration_reasoning,
        "entry_conditions": entry_conditions,
        "exit_conditions": exit_conditions,
        "adverse_scenario": adverse_scenario,
        "spot_price_at_analysis": spot_price,
        "expiration_date": expiry_date,
        "days_to_expiry": days_to_expiry,
        "max_profit": risk_metrics.get("max_profit"),
        "max_loss": risk_metrics.get("max_loss"),
        "breakeven_prices": risk_metrics.get("breakeven_prices", []),
        "capital_required": risk_metrics.get("capital_required"),
        "margin_requirement": margin,
        "risk_reward_ratio": risk_metrics.get("risk_reward_ratio"),
        "risk_score": risk_assessment["risk_score"],
        "has_unlimited_risk": risk_assessment["has_unlimited_risk"],
        "has_assignment_risk": risk_assessment["has_assignment_risk"],
        "has_high_gamma": risk_assessment["has_high_gamma"],
        "has_volatility_sensitivity": risk_assessment["has_volatility_sensitivity"],
        "legs": enriched_legs,
    }


# --- Dispatcher ---

TOOL_HANDLERS = {
    "get_stock_quote": handle_get_stock_quote,
    "get_stock_history": handle_get_stock_history,
    "get_stock_news": handle_get_stock_news,
    "get_portfolio_holdings": handle_get_portfolio_holdings,
    "get_portfolio_summary": handle_get_portfolio_summary,
    "get_options_expirations": handle_get_options_expirations,
    "get_options_chain": handle_get_options_chain,
    "generate_options_strategy": handle_generate_options_strategy,
}


def dispatch_tool(tool_name: str, tool_input: dict, portfolio_id: UUID) -> dict:
    """Route a tool call to its handler."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}

    # Inject portfolio_id for portfolio-scoped tools
    if tool_name in ("get_portfolio_holdings", "get_portfolio_summary"):
        tool_input["portfolio_id"] = portfolio_id

    return handler(**tool_input)
