"""Chat session CRUD and message orchestration."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_supabase


def create_session(portfolio_id: UUID, title: str | None = None) -> dict:
    db = get_supabase()
    result = db.table("chat_sessions").insert({
        "portfolio_id": str(portfolio_id),
        "title": title,
    }).execute()
    return result.data[0]


def list_sessions(portfolio_id: UUID) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("chat_sessions")
        .select("*")
        .eq("portfolio_id", str(portfolio_id))
        .order("updated_at", desc=True)
        .execute()
    )
    sessions = result.data

    # Add last message preview
    for session in sessions:
        msg_result = (
            db.table("chat_messages")
            .select("content, role")
            .eq("session_id", session["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if msg_result.data:
            preview = msg_result.data[0]["content"][:100]
            session["last_message_preview"] = preview
        else:
            session["last_message_preview"] = None

    return sessions


def get_session(session_id: UUID) -> dict | None:
    db = get_supabase()
    result = (
        db.table("chat_sessions")
        .select("*")
        .eq("id", str(session_id))
        .execute()
    )
    if not result.data:
        return None
    session = result.data[0]

    # Get messages
    msg_result = (
        db.table("chat_messages")
        .select("*")
        .eq("session_id", str(session_id))
        .order("created_at", desc=False)
        .execute()
    )
    messages = msg_result.data

    # Get recommendations for messages that have them
    for msg in messages:
        msg["recommendations"] = []
        if msg.get("has_recommendation"):
            rec_result = (
                db.table("options_recommendations")
                .select("*")
                .eq("message_id", msg["id"])
                .execute()
            )
            for rec in rec_result.data:
                # Get legs
                legs_result = (
                    db.table("options_recommendation_legs")
                    .select("*")
                    .eq("recommendation_id", rec["id"])
                    .order("leg_order", desc=False)
                    .execute()
                )
                rec["legs"] = legs_result.data

                # Get decision
                dec_result = (
                    db.table("options_decisions")
                    .select("*")
                    .eq("recommendation_id", rec["id"])
                    .execute()
                )
                rec["decision"] = dec_result.data[0] if dec_result.data else None

                msg["recommendations"].append(rec)

    session["messages"] = messages
    return session


def delete_session(session_id: UUID) -> bool:
    db = get_supabase()
    result = (
        db.table("chat_sessions")
        .delete()
        .eq("id", str(session_id))
        .execute()
    )
    return bool(result.data)


def add_message(session_id: UUID, role: str, content: str, has_recommendation: bool = False) -> dict:
    db = get_supabase()
    result = db.table("chat_messages").insert({
        "session_id": str(session_id),
        "role": role,
        "content": content,
        "has_recommendation": has_recommendation,
    }).execute()

    # Touch session updated_at
    db.table("chat_sessions").update({
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", str(session_id)).execute()

    return result.data[0]


def get_session_messages(session_id: UUID) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("chat_messages")
        .select("*")
        .eq("session_id", str(session_id))
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


def update_title(session_id: UUID, title: str):
    db = get_supabase()
    db.table("chat_sessions").update({
        "title": title,
    }).eq("id", str(session_id)).execute()


def store_recommendation(
    message_id: UUID,
    session_id: UUID,
    recommendation: dict,
) -> dict:
    """Store an options recommendation and its legs in the database."""
    db = get_supabase()

    rec_data = {
        "message_id": str(message_id),
        "session_id": str(session_id),
        "ticker": recommendation["ticker"],
        "strategy_type": recommendation["strategy_type"],
        "strategy_name": recommendation["strategy_name"],
        "confidence_score": recommendation.get("confidence_score"),
        "strategy_reasoning": recommendation.get("strategy_reasoning"),
        "strike_reasoning": recommendation.get("strike_reasoning"),
        "expiration_reasoning": recommendation.get("expiration_reasoning"),
        "entry_conditions": recommendation.get("entry_conditions"),
        "exit_conditions": recommendation.get("exit_conditions"),
        "adverse_scenario": recommendation.get("adverse_scenario"),
        "max_profit": recommendation.get("max_profit"),
        "max_loss": recommendation.get("max_loss"),
        "breakeven_prices": recommendation.get("breakeven_prices", []),
        "capital_required": recommendation.get("capital_required"),
        "margin_requirement": recommendation.get("margin_requirement"),
        "risk_reward_ratio": recommendation.get("risk_reward_ratio"),
        "risk_score": recommendation.get("risk_score"),
        "has_unlimited_risk": recommendation.get("has_unlimited_risk", False),
        "has_assignment_risk": recommendation.get("has_assignment_risk", False),
        "has_high_gamma": recommendation.get("has_high_gamma", False),
        "has_volatility_sensitivity": recommendation.get("has_volatility_sensitivity", False),
        "spot_price_at_analysis": recommendation.get("spot_price_at_analysis"),
        "expiration_date": recommendation.get("expiration_date"),
        "days_to_expiry": recommendation.get("days_to_expiry"),
    }

    rec_result = db.table("options_recommendations").insert(rec_data).execute()
    rec = rec_result.data[0]

    # Store legs
    for leg in recommendation.get("legs", []):
        db.table("options_recommendation_legs").insert({
            "recommendation_id": rec["id"],
            "leg_order": leg.get("leg_order", 1),
            "action": leg["action"],
            "option_type": leg["option_type"],
            "strike": leg["strike"],
            "contracts": leg.get("contracts", 1),
            "premium": leg.get("premium"),
            "bid": leg.get("bid"),
            "ask": leg.get("ask"),
            "implied_volatility": leg.get("implied_volatility"),
            "open_interest": leg.get("open_interest"),
            "volume": leg.get("volume"),
            "delta": leg.get("delta"),
            "gamma": leg.get("gamma"),
            "theta": leg.get("theta"),
            "vega": leg.get("vega"),
        }).execute()

    return rec


def record_decision(recommendation_id: UUID, decision: str, notes: str = "") -> dict:
    db = get_supabase()
    result = db.table("options_decisions").insert({
        "recommendation_id": str(recommendation_id),
        "decision": decision,
        "notes": notes,
    }).execute()
    return result.data[0]
