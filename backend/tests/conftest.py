"""Shared fixtures for backend tests."""
from __future__ import annotations

import os
import sys
from uuid import UUID

import pytest

# Ensure backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Dummy environment variables so settings don't fail on import
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


FAKE_PORTFOLIO_ID = UUID("00000000-0000-0000-0000-000000000001")
FAKE_SESSION_ID = UUID("00000000-0000-0000-0000-000000000002")
FAKE_MESSAGE_ID = UUID("00000000-0000-0000-0000-000000000003")
FAKE_REC_ID = UUID("00000000-0000-0000-0000-000000000004")


@pytest.fixture
def portfolio_id():
    return FAKE_PORTFOLIO_ID


@pytest.fixture
def session_id():
    return FAKE_SESSION_ID
