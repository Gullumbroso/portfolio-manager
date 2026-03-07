"""Chat API endpoints with SSE streaming."""
from __future__ import annotations
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    SessionCreate,
    SessionResponse,
    SessionDetailResponse,
    MessageCreate,
    DecisionCreate,
    DecisionResponse,
)
from app.services.ai import chat_service, ai_engine

router = APIRouter()


@router.post("/{portfolio_id}/chat/sessions", response_model=SessionResponse)
def create_session(portfolio_id: UUID, body: SessionCreate = SessionCreate()):
    session = chat_service.create_session(portfolio_id, body.title)
    session["last_message_preview"] = None
    return session


@router.get("/{portfolio_id}/chat/sessions", response_model=list[SessionResponse])
def list_sessions(portfolio_id: UUID):
    return chat_service.list_sessions(portfolio_id)


@router.get("/{portfolio_id}/chat/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(portfolio_id: UUID, session_id: UUID):
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session["portfolio_id"]) != str(portfolio_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{portfolio_id}/chat/sessions/{session_id}")
def delete_session(portfolio_id: UUID, session_id: UUID):
    deleted = chat_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/{portfolio_id}/chat/sessions/{session_id}/messages")
def send_message(portfolio_id: UUID, session_id: UUID, body: MessageCreate):
    # Verify session exists
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user message
    chat_service.add_message(session_id, "user", body.content)

    # Build message history for Claude
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in session["messages"]
    ]
    messages.append({"role": "user", "content": body.content})

    def event_stream():
        full_text = ""
        recommendations = []

        try:
            gen = ai_engine.stream_chat(portfolio_id, messages)
            for event in gen:
                if event["event"] == "text":
                    full_text += event["data"]["content"]
                elif event["event"] == "recommendation":
                    recommendations.append(event["data"]["recommendation"])

                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            return

        # Store assistant message
        has_rec = len(recommendations) > 0
        assistant_msg = chat_service.add_message(
            session_id, "assistant", full_text, has_recommendation=has_rec
        )

        # Store recommendations
        for rec in recommendations:
            chat_service.store_recommendation(
                message_id=assistant_msg["id"],
                session_id=str(session_id),
                recommendation=rec,
            )

        # Auto-generate title after first exchange
        all_messages = messages + [{"role": "assistant", "content": full_text}]
        if len(all_messages) == 2 and not session.get("title"):
            try:
                title = ai_engine.generate_session_title(all_messages)
                chat_service.update_title(session_id, title)
                yield f"event: title_update\ndata: {json.dumps({'title': title})}\n\n"
            except Exception:
                pass

        yield f"event: done\ndata: {json.dumps({'message_id': assistant_msg['id']})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{portfolio_id}/chat/recommendations/{recommendation_id}/decision", response_model=DecisionResponse)
def record_decision(portfolio_id: UUID, recommendation_id: UUID, body: DecisionCreate):
    try:
        return chat_service.record_decision(recommendation_id, body.decision, body.notes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
