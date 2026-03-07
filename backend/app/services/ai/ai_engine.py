"""Claude AI integration with streaming and tool dispatch."""
from __future__ import annotations
import json
from typing import Generator
from uuid import UUID

import anthropic

from app.config import get_settings
from app.services.ai.tools import TOOL_DEFINITIONS, dispatch_tool
from app.services.holding_service import get_holdings, get_portfolio_summary


def _get_client() -> anthropic.Anthropic:
    settings = get_settings()
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _build_system_prompt(portfolio_id: UUID) -> str:
    """Build system prompt with portfolio context."""
    try:
        holdings = get_holdings(portfolio_id)
        summary = get_portfolio_summary(portfolio_id)
    except Exception:
        holdings = []
        summary = {}

    holdings_text = "No holdings yet."
    if holdings:
        lines = []
        for h in holdings:
            price_str = f"${h['current_price']:.2f}" if h.get("current_price") else "N/A"
            gain_str = ""
            if h.get("total_gain_dollars") is not None:
                sign = "+" if h["total_gain_dollars"] >= 0 else ""
                gain_str = f" ({sign}${h['total_gain_dollars']:.2f}, {sign}{h['total_gain_percent']:.1f}%)"
            lines.append(
                f"  - {h['ticker']}: {h['total_shares']} shares @ avg ${h['avg_cost_per_share']:.2f}, "
                f"current {price_str}{gain_str}"
            )
        holdings_text = "\n".join(lines)

    cash = summary.get("cash_balance", 0)
    total = summary.get("total_value", 0)
    profit = summary.get("profit_dollars", 0)
    profit_pct = summary.get("profit_percent", 0)

    return f"""You are an expert investment consultant for the user's portfolio. You have access to real-time market data, portfolio analytics, and options analysis tools.

PORTFOLIO CONTEXT:
Holdings:
{holdings_text}

Cash balance: ${cash:,.2f}
Total portfolio value: ${total:,.2f}
Total profit: ${profit:,.2f} ({profit_pct:+.1f}%)

CAPABILITIES:
- Discuss any stock, sector, or market topic
- Analyze portfolio allocation, risk, and diversification
- Look up real-time quotes, price history, and news
- Analyze options chains and generate specific strategy recommendations
- Compute risk metrics for options strategies

GUIDELINES:
- Be conversational and helpful. Ask clarifying questions when the user's intent is unclear.
- When discussing options, use the tools to fetch real data before making recommendations.
- For options recommendations, always use generate_options_strategy to provide structured output with computed Greeks and risk metrics.
- Explain your reasoning clearly. Reference specific numbers and data.
- Flag risks prominently. Never downplay potential losses.
- If a ticker has no options available, say so clearly.
- Keep responses focused and not overly long. Use markdown formatting for readability."""


def stream_chat(
    portfolio_id: UUID,
    messages: list[dict],
) -> Generator[dict, None, None]:
    """Stream a chat response from Claude, handling tool calls.

    Yields SSE event dicts.
    """
    client = _get_client()
    settings = get_settings()
    system_prompt = _build_system_prompt(portfolio_id)

    # Convert messages to Claude format
    claude_messages = []
    for msg in messages:
        claude_messages.append({"role": msg["role"], "content": msg["content"]})

    full_text = ""
    recommendations = []

    # Loop to handle multi-turn tool use
    while True:
        collected_text = ""
        tool_uses = []

        with client.messages.stream(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=system_prompt,
            messages=claude_messages,
            tools=TOOL_DEFINITIONS,
        ) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        tool_uses.append({
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input_json": "",
                        })
                        yield {
                            "event": "tool_start",
                            "data": {"tool": event.content_block.name},
                        }

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        collected_text += event.delta.text
                        yield {
                            "event": "text",
                            "data": {"content": event.delta.text},
                        }
                    elif event.delta.type == "input_json_delta":
                        if tool_uses:
                            tool_uses[-1]["input_json"] += event.delta.partial_json

            # Get the final message for stop reason
            final_message = stream.get_final_message()

        full_text += collected_text

        # Check if we need to handle tool calls
        if final_message.stop_reason != "tool_use" or not tool_uses:
            break

        # Process tool calls
        # Add assistant message with content blocks
        assistant_content = []
        if collected_text:
            assistant_content.append({"type": "text", "text": collected_text})
        for tu in tool_uses:
            try:
                tool_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
            except json.JSONDecodeError:
                tool_input = {}
            assistant_content.append({
                "type": "tool_use",
                "id": tu["id"],
                "name": tu["name"],
                "input": tool_input,
            })

        claude_messages.append({"role": "assistant", "content": assistant_content})

        # Execute tools and build tool results
        tool_results = []
        for tu in tool_uses:
            try:
                tool_input = json.loads(tu["input_json"]) if tu["input_json"] else {}
            except json.JSONDecodeError:
                tool_input = {}

            result = dispatch_tool(tu["name"], tool_input, portfolio_id)

            # If it's a strategy recommendation, emit it and track it
            if tu["name"] == "generate_options_strategy" and "error" not in result:
                recommendations.append(result)
                yield {
                    "event": "recommendation",
                    "data": {"recommendation": result},
                }

            yield {
                "event": "tool_result",
                "data": {
                    "tool": tu["name"],
                    "summary": _summarize_tool_result(tu["name"], result),
                },
            }

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": json.dumps(result),
            })

        claude_messages.append({"role": "user", "content": tool_results})



def _summarize_tool_result(tool_name: str, result: dict) -> str:
    """Create a brief summary of a tool result for the UI."""
    if "error" in result:
        return f"Error: {result['error']}"

    if tool_name == "get_stock_quote":
        return f"{result.get('ticker', '?')}: ${result.get('price', 0):.2f} ({result.get('change_percent', 0):+.2f}%)"
    if tool_name == "get_stock_history":
        return f"{result.get('ticker', '?')} {result.get('period', '')}: {result.get('price_change_pct', 0):+.2f}%"
    if tool_name == "get_stock_news":
        return f"{result.get('article_count', 0)} articles for {result.get('ticker', '?')}"
    if tool_name == "get_portfolio_holdings":
        return f"{result.get('count', 0)} holdings"
    if tool_name == "get_portfolio_summary":
        return f"Portfolio: ${result.get('total_value', 0):,.2f}"
    if tool_name == "get_options_expirations":
        exps = result.get("expirations", [])
        return f"{len(exps)} expiration dates available"
    if tool_name == "get_options_chain":
        return f"Options chain for {result.get('ticker', '?')} exp {result.get('expiry_date', '?')}"
    if tool_name == "generate_options_strategy":
        return f"Strategy: {result.get('strategy_name', '?')}"
    return "Done"


def generate_session_title(messages: list[dict]) -> str:
    """Ask Claude for a short session title based on the conversation."""
    client = _get_client()
    settings = get_settings()

    # Take first few messages
    context = messages[:4]
    prompt_messages = [
        {"role": "user", "content": (
            "Based on this conversation, generate a very short title (3-6 words, no quotes):\n\n"
            + "\n".join(f"{m['role']}: {m['content'][:200]}" for m in context)
        )}
    ]

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=30,
        messages=prompt_messages,
    )
    return response.content[0].text.strip().strip('"\'')
