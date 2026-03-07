"""Tests for chat API router endpoints."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app


FAKE_PORTFOLIO_ID = "00000000-0000-0000-0000-000000000001"
FAKE_SESSION_ID = "00000000-0000-0000-0000-000000000002"
FAKE_MESSAGE_ID = "00000000-0000-0000-0000-000000000003"
FAKE_REC_ID = "00000000-0000-0000-0000-000000000004"

client = TestClient(app)


# ---------------------------------------------------------------------------
# 6.1  Session CRUD
# ---------------------------------------------------------------------------

class TestSessionCRUD:
    @patch("app.routers.chat.chat_service")
    def test_create_session(self, mock_svc):
        mock_svc.create_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "title": None,
            "status": "active",
            "created_at": "2026-03-07T00:00:00Z",
            "updated_at": "2026-03-07T00:00:00Z",
        }
        resp = client.post(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions")
        assert resp.status_code == 200
        assert resp.json()["id"] == FAKE_SESSION_ID

    @patch("app.routers.chat.chat_service")
    def test_list_sessions(self, mock_svc):
        mock_svc.list_sessions.return_value = [{
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "title": "Test",
            "status": "active",
            "created_at": "2026-03-07T00:00:00Z",
            "updated_at": "2026-03-07T00:00:00Z",
            "last_message_preview": "Hello",
        }]
        resp = client.get(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("app.routers.chat.chat_service")
    def test_get_session_with_messages(self, mock_svc):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "title": "Test",
            "status": "active",
            "created_at": "2026-03-07T00:00:00Z",
            "updated_at": "2026-03-07T00:00:00Z",
            "messages": [{
                "id": FAKE_MESSAGE_ID,
                "session_id": FAKE_SESSION_ID,
                "role": "user",
                "content": "Hello",
                "has_recommendation": False,
                "created_at": "2026-03-07T00:00:00Z",
                "recommendations": [],
            }],
        }
        resp = client.get(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}")
        assert resp.status_code == 200
        assert len(resp.json()["messages"]) == 1

    @patch("app.routers.chat.chat_service")
    def test_get_session_not_found(self, mock_svc):
        mock_svc.get_session.return_value = None
        resp = client.get(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}")
        assert resp.status_code == 404

    @patch("app.routers.chat.chat_service")
    def test_get_session_wrong_portfolio(self, mock_svc):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": "99999999-9999-9999-9999-999999999999",  # different
        }
        resp = client.get(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}")
        assert resp.status_code == 404

    @patch("app.routers.chat.chat_service")
    def test_delete_session(self, mock_svc):
        mock_svc.delete_session.return_value = True
        resp = client.delete(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    @patch("app.routers.chat.chat_service")
    def test_delete_session_not_found(self, mock_svc):
        mock_svc.delete_session.return_value = False
        resp = client.delete(f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 6.2  Send Message (SSE streaming)
# ---------------------------------------------------------------------------

class TestSendMessage:
    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_streams_sse_response(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "messages": [],
            "title": "Test",
        }
        mock_svc.add_message.return_value = {"id": FAKE_MESSAGE_ID}
        mock_ai.stream_chat.return_value = iter([
            {"event": "text", "data": {"content": "Hello"}},
        ])

        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "hi"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        assert "event: text" in body
        assert "event: done" in body

    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_user_message_stored(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "messages": [],
            "title": "Test",
        }
        mock_svc.add_message.return_value = {"id": FAKE_MESSAGE_ID}
        mock_ai.stream_chat.return_value = iter([])

        client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "hi"},
        )
        # First add_message call is for user message
        first_call = mock_svc.add_message.call_args_list[0]
        assert first_call[0][1] == "user"
        assert first_call[0][2] == "hi"

    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_assistant_message_stored_after_stream(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "messages": [],
            "title": "Test",
        }
        mock_svc.add_message.return_value = {"id": FAKE_MESSAGE_ID}
        mock_ai.stream_chat.return_value = iter([
            {"event": "text", "data": {"content": "Hello world"}},
        ])

        client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "hi"},
        )
        # Second add_message call is for assistant message
        assert mock_svc.add_message.call_count == 2
        second_call = mock_svc.add_message.call_args_list[1]
        assert second_call[0][1] == "assistant"
        assert "Hello world" in second_call[0][2]

    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_recommendation_stored(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "messages": [],
            "title": "Test",
        }
        mock_svc.add_message.return_value = {"id": FAKE_MESSAGE_ID}
        rec_data = {"ticker": "AAPL", "strategy_name": "Bull Call"}
        mock_ai.stream_chat.return_value = iter([
            {"event": "recommendation", "data": {"recommendation": rec_data}},
        ])

        client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "strategy"},
        )
        mock_svc.store_recommendation.assert_called_once()

    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_session_not_found(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = None
        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "hi"},
        )
        assert resp.status_code == 404

    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_title_generated_on_first_exchange(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "messages": [],  # no existing messages → first exchange
            "title": None,   # no title yet
        }
        mock_svc.add_message.return_value = {"id": FAKE_MESSAGE_ID}
        mock_ai.stream_chat.return_value = iter([
            {"event": "text", "data": {"content": "AAPL is at $185"}},
        ])
        mock_ai.generate_session_title.return_value = "AAPL Price Check"

        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "What's AAPL at?"},
        )
        assert "title_update" in resp.text
        mock_svc.update_title.assert_called_once()

    @patch("app.routers.chat.ai_engine")
    @patch("app.routers.chat.chat_service")
    def test_error_during_streaming(self, mock_svc, mock_ai):
        mock_svc.get_session.return_value = {
            "id": FAKE_SESSION_ID,
            "portfolio_id": FAKE_PORTFOLIO_ID,
            "messages": [],
            "title": "Test",
        }
        mock_svc.add_message.return_value = {"id": FAKE_MESSAGE_ID}
        mock_ai.stream_chat.side_effect = Exception("AI broke")

        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/sessions/{FAKE_SESSION_ID}/messages",
            json={"content": "hi"},
        )
        assert resp.status_code == 200  # SSE still returns 200
        assert "event: error" in resp.text


# ---------------------------------------------------------------------------
# 6.3  Decisions
# ---------------------------------------------------------------------------

class TestDecisions:
    @patch("app.routers.chat.chat_service")
    def test_accept_recommendation(self, mock_svc):
        mock_svc.record_decision.return_value = {
            "id": "00000000-0000-0000-0000-000000000099",
            "recommendation_id": FAKE_REC_ID,
            "decision": "accepted",
            "notes": "",
            "created_at": "2026-03-07T00:00:00Z",
        }
        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/recommendations/{FAKE_REC_ID}/decision",
            json={"decision": "accepted"},
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "accepted"

    @patch("app.routers.chat.chat_service")
    def test_reject_with_notes(self, mock_svc):
        mock_svc.record_decision.return_value = {
            "id": "00000000-0000-0000-0000-000000000099",
            "recommendation_id": FAKE_REC_ID,
            "decision": "rejected",
            "notes": "Too risky",
            "created_at": "2026-03-07T00:00:00Z",
        }
        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/recommendations/{FAKE_REC_ID}/decision",
            json={"decision": "rejected", "notes": "Too risky"},
        )
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Too risky"

    @patch("app.routers.chat.chat_service")
    def test_invalid_recommendation(self, mock_svc):
        mock_svc.record_decision.side_effect = Exception("Not found")
        resp = client.post(
            f"/api/portfolios/{FAKE_PORTFOLIO_ID}/chat/recommendations/{FAKE_REC_ID}/decision",
            json={"decision": "accepted"},
        )
        assert resp.status_code == 400
