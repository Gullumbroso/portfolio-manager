# AI Consultant Test Plan

## Overview

Tests for the AI Investment Consultant feature covering: options quantitative engines, tool handlers, AI engine streaming, chat API routes, DB persistence, frontend components/hooks, and live AI integration tests.

**Test framework:** pytest (backend), Vitest + React Testing Library (frontend), Playwright (E2E)

---

## 1. Quant Engine — Unit Tests

**File:** `backend/tests/test_quant_engine.py`
**Source:** `backend/app/services/options/quant_engine.py`
**Dependencies:** None (pure math)

### 1.1 `black_scholes_price`
| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | ATM call | S=100, K=100, T=0.25, sigma=0.3 | ~6.33 (known BS value) |
| 2 | Deep ITM put | S=80, K=100, T=0.25, sigma=0.3 | Close to intrinsic (20 - time value) |
| 3 | At expiry (T=0) call ITM | S=110, K=100, T=0, sigma=0.3 | Exactly 10 (intrinsic) |
| 4 | At expiry (T=0) call OTM | S=90, K=100, T=0, sigma=0.3 | Exactly 0 |
| 5 | Zero IV | S=100, K=100, T=0.25, sigma=0 | Intrinsic value |
| 6 | Put-call parity | Same params | C - P = S - K*e^(-rT) |

### 1.2 `compute_greeks`
| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | ATM call delta | S=100, K=100, T=0.25, sigma=0.3 | ~0.55 (slightly above 0.5) |
| 2 | ATM put delta | Same as above, put | ~-0.45 |
| 3 | Gamma positive | Any option | gamma > 0 |
| 4 | Call theta negative | Any call | theta < 0 (time decay) |
| 5 | Vega positive | Any option | vega > 0 |
| 6 | Deep ITM call delta | S=200, K=100 | Close to 1.0 |
| 7 | Deep OTM call delta | S=50, K=100 | Close to 0.0 |
| 8 | At expiry (T=0) ITM | S=110, K=100, T=0, call | delta=1.0, gamma=0, theta=0, vega=0 |
| 9 | At expiry (T=0) OTM | S=90, K=100, T=0, call | delta=0.0, gamma=0, theta=0, vega=0 |
| 10 | Near-expiry high gamma | T=1/365, ATM | gamma much larger than T=0.25 |

### 1.3 `compute_strategy_risk`
| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Long call | buy call K=100, premium=5 | max_loss=-500, max_profit=inf (None), breakeven=105 |
| 2 | Long put | buy put K=100, premium=3 | max_loss=-300, breakeven=97 |
| 3 | Bull call spread | buy call K=100 prem=5, sell call K=110 prem=2 | max_loss=-300, max_profit=700, breakeven~103 |
| 4 | Bear put spread | buy put K=110 prem=6, sell put K=100 prem=2 | max_loss=-400, max_profit=600, breakeven~106 |
| 5 | Iron condor | sell put K=90, buy put K=85, sell call K=110, buy call K=115 | max_loss capped, max_profit=net credit, 2 breakevens |
| 6 | Naked call (unlimited risk) | sell call K=100, premium=5 | max_profit=500, max_loss=None (unlimited) |
| 7 | Straddle | buy call K=100 prem=5, buy put K=100 prem=5 | max_loss=-1000, 2 breakevens (90, 110) |
| 8 | Empty legs | [] | {} |
| 9 | Multi-contract | buy 3 calls K=100 prem=5 | max_loss=-1500 (scaled by contracts) |

### 1.4 `compute_margin_requirement`
| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Long call only (no short) | buy call K=100 | 0 (no margin for long) |
| 2 | Naked call | sell call K=100, spot=100 | max(20%*100*100 - 0 + prem*100, 10%*100*100 + prem*100) |
| 3 | Naked put | sell put K=100, spot=100 | Calculated per formula |
| 4 | Spread (reduced margin) | bull call spread | min(naked margin, abs(max_loss)) |
| 5 | OTM naked call | sell call K=120, spot=100 | Lower than ATM due to OTM offset |

---

## 2. Risk Engine — Unit Tests

**File:** `backend/tests/test_risk_engine.py`
**Source:** `backend/app/services/options/risk_engine.py`
**Dependencies:** None (pure logic)

### 2.1 `assess_risk`
| # | Test | Expected |
|---|------|----------|
| 1 | Long call, 30 DTE, OTM | score=3, all flags false |
| 2 | Naked call, 30 DTE, OTM | score=9, unlimited_risk=true |
| 3 | Naked call, 5 DTE, OTM | score=10 (9 base, capped to 8 by unlimited, +1 gamma, +1... clamped to 10) |
| 4 | Bull call spread, 30 DTE, OTM | score=4, all flags false |
| 5 | Iron condor, short leg ITM, 5 DTE | score=5+1(gamma)+1(assignment)=7 |
| 6 | Short calls without long calls (not labeled naked_call) | unlimited_risk=true (detected by leg analysis) |
| 7 | Short ITM call | assignment_risk=true |
| 8 | Short OTM call | assignment_risk=false |
| 9 | Short ITM put | assignment_risk=true |
| 10 | Net vega > 0.5 | vol_sensitivity=true |
| 11 | Net vega < 0.5 | vol_sensitivity=false |
| 12 | Unknown strategy_type | base score defaults to 5 |

---

## 3. Options Data Service — Unit Tests (mocked yfinance)

**File:** `backend/tests/test_options_data_service.py`
**Source:** `backend/app/services/options/options_data_service.py`
**Dependencies:** Mock `yfinance.Ticker`

| # | Test | Expected |
|---|------|----------|
| 1 | `get_available_expirations` — valid ticker | Returns list of date strings |
| 2 | `get_available_expirations` — invalid ticker | Returns [] |
| 3 | `get_options_chain` — parses DataFrame | Returns calls/puts with correct fields (strike, bid, ask, IV, volume, OI, inTheMoney) |
| 4 | `get_options_chain` — handles NaN volume/OI | Returns 0 instead of NaN |
| 5 | `get_chain_summary` — ATM filtering | Spot=150, strikes 100-200 → returns ~20 strikes nearest to 150 |
| 6 | `get_chain_summary` — spot between strikes | Spot=152.50, nearest strikes on both sides included |
| 7 | `get_chain_summary` — few strikes available | Returns all if fewer than num_strikes*2 |

---

## 4. Tool Handlers — Integration Tests (mocked external services)

**File:** `backend/tests/test_tool_handlers.py`
**Source:** `backend/app/services/ai/tools.py`
**Dependencies:** Mock `market_data_service`, `holding_service`, `options_data_service`

### 4.1 Stock Tools
| # | Test | Mock | Expected |
|---|------|------|----------|
| 1 | `get_stock_quote` — success | get_quote returns price data | Returns ticker, price, change |
| 2 | `get_stock_quote` — invalid ticker | get_quote raises | Returns {error: ...} |
| 3 | `get_stock_history` — success | get_history returns data | Returns data_points, price_change, price_change_pct |
| 4 | `get_stock_history` — empty data | get_history returns [] | Returns {error: ...} |
| 5 | `get_stock_news` — has articles | get_news returns 15 articles | Returns max 10 articles |
| 6 | `get_stock_news` — no articles | get_news returns [] | Returns {articles: [], message: ...} |
| 7 | `get_portfolio_holdings` — has holdings | get_holdings returns list | Returns holdings + count |
| 8 | `get_portfolio_holdings` — empty | get_holdings returns [] | Returns {holdings: [], message: ...} |
| 9 | `get_portfolio_summary` | get_portfolio_summary returns data | Returns summary as-is |

### 4.2 Options Tools
| # | Test | Mock | Expected |
|---|------|------|----------|
| 1 | `get_options_expirations` — success | Returns dates | Returns ticker + expirations |
| 2 | `get_options_expirations` — no options | Returns [] | Returns {error: ...} |
| 3 | `get_options_chain` — success | get_chain_summary returns data | Returns chain data |
| 4 | `get_options_chain` — error | get_chain_summary raises | Returns {error: ...} |

### 4.3 `generate_options_strategy` — Full Pipeline
| # | Test | Setup | Expected |
|---|------|-------|----------|
| 1 | Long call — enriched with Greeks | Mock quote + chain | Legs have delta/gamma/theta/vega computed server-side (not from AI) |
| 2 | Bull call spread — risk metrics | Mock quote + chain | max_profit, max_loss, breakevens, risk_reward all present and computed |
| 3 | Iron condor — 4 legs enriched | Mock quote + chain | All 4 legs have Greeks, risk_score present |
| 4 | Naked call — unlimited risk flagged | Mock quote + chain | has_unlimited_risk=true, risk_score >= 8 |
| 5 | Near-expiry strategy — high gamma | expiry_date=3 days out | has_high_gamma=true |
| 6 | Expired date rejected | expiry_date in the past | Returns {error: "...in the past"} |
| 7 | Invalid date format | expiry_date="not-a-date" | Returns {error: "Invalid date format..."} |
| 8 | Chain data unavailable — falls back | get_chain_summary raises | Uses default IV=0.3, still computes Greeks |
| 9 | Margin computed | Naked call setup | margin_requirement > 0 |
| 10 | Spot price captured | Mock quote at $150 | spot_price_at_analysis=150 |
| 11 | Reasoning fields passed through | Provide strategy_reasoning etc. | All reasoning fields in output |

### 4.4 `dispatch_tool`
| # | Test | Expected |
|---|------|----------|
| 1 | Known tool dispatches correctly | Calls right handler |
| 2 | Unknown tool name | Returns {error: "Unknown tool: ..."} |
| 3 | Portfolio-scoped tools get portfolio_id injected | portfolio_id in kwargs |

---

## 5. AI Engine — Integration Tests (mocked Anthropic client)

**File:** `backend/tests/test_ai_engine.py`
**Source:** `backend/app/services/ai/ai_engine.py`
**Dependencies:** Mock `anthropic.Anthropic`, mock tool handlers

### 5.1 `_build_system_prompt`
| # | Test | Expected |
|---|------|----------|
| 1 | With holdings | Prompt contains ticker names, share counts, prices |
| 2 | Empty portfolio | Prompt contains "No holdings yet." |
| 3 | Holdings fetch fails | Prompt still generates (graceful fallback) |
| 4 | Contains cash balance and total value | Dollar amounts present |

### 5.2 `stream_chat`
| # | Test | Expected |
|---|------|----------|
| 1 | Text-only response | Yields: text events → (no tool events) |
| 2 | Single tool call | Yields: tool_start → tool_result → text → (stop_reason=end_turn) |
| 3 | Multi-turn tool use | Claude calls tool → gets result → calls another tool → final text |
| 4 | Recommendation emitted | generate_options_strategy called → yields recommendation event with full structured data |
| 5 | Tool error handled | Tool returns {error: ...} → tool_result event with error summary → Claude continues |
| 6 | Anthropic API error | Client raises exception → yields error event |

### 5.3 `generate_session_title`
| # | Test | Expected |
|---|------|----------|
| 1 | Returns short title | 3-6 words, no quotes |
| 2 | Based on conversation content | Mock Claude returns relevant title |

---

## 6. Chat Router — API Tests (mocked services)

**File:** `backend/tests/test_chat_router.py`
**Source:** `backend/app/routers/chat.py`
**Dependencies:** Mock `chat_service`, `ai_engine`; use FastAPI TestClient

### 6.1 Session CRUD
| # | Test | Expected |
|---|------|----------|
| 1 | POST create session | 200, returns session with id |
| 2 | GET list sessions | 200, returns array |
| 3 | GET session with messages | 200, includes messages + recommendations |
| 4 | GET session — not found | 404 |
| 5 | GET session — wrong portfolio_id | 404 |
| 6 | DELETE session | 200, {ok: true} |
| 7 | DELETE session — not found | 404 |

### 6.2 Send Message (SSE streaming)
| # | Test | Expected |
|---|------|----------|
| 1 | Sends message, streams response | SSE format: `event: text\ndata: {...}\n\n` |
| 2 | User message stored in DB | chat_service.add_message called with role="user" |
| 3 | Assistant message stored after stream | chat_service.add_message called with role="assistant", full text |
| 4 | Recommendation stored in DB | chat_service.store_recommendation called with enriched data |
| 5 | Title auto-generated on first exchange | chat_service.update_title called, title_update event emitted |
| 6 | Title NOT generated on subsequent messages | Only when len(all_messages) == 2 and no existing title |
| 7 | Error during streaming | Yields error event, no crash |
| 8 | Session not found | 404 |

### 6.3 Decisions
| # | Test | Expected |
|---|------|----------|
| 1 | Accept recommendation | 200, decision="accepted" stored |
| 2 | Reject with notes | 200, decision="rejected", notes stored |
| 3 | Invalid recommendation_id | 400 |

---

## 7. Chat Service — Integration Tests (mocked Supabase)

**File:** `backend/tests/test_chat_service.py`
**Source:** `backend/app/services/ai/chat_service.py`
**Dependencies:** Mock `get_supabase`

| # | Test | Expected |
|---|------|----------|
| 1 | `create_session` | Inserts into chat_sessions, returns record |
| 2 | `list_sessions` | Queries by portfolio_id, ordered by updated_at DESC, includes last_message_preview |
| 3 | `get_session` — with messages and recommendations | Fetches session + messages + recs + legs + decisions, nested correctly |
| 4 | `get_session` — not found | Returns None |
| 5 | `delete_session` | Deletes from chat_sessions, returns True |
| 6 | `add_message` | Inserts message, touches session updated_at |
| 7 | `update_title` | Updates session title |
| 8 | `store_recommendation` — with legs | Inserts into options_recommendations + options_recommendation_legs |
| 9 | `store_recommendation` — all fields mapped | All 20+ fields from recommendation dict correctly mapped to DB columns |
| 10 | `record_decision` | Inserts into options_decisions |

---

## 8. Frontend Components — Unit Tests

**File:** `frontend/src/components/**/*.test.tsx`
**Dependencies:** Vitest, React Testing Library

### 8.1 Chat Components
| # | Component | Test | Expected |
|---|-----------|------|----------|
| 1 | ChatMessage | User message styling | Right-aligned, primary color |
| 2 | ChatMessage | Assistant message with markdown | Left-aligned, renders markdown |
| 3 | ChatMessage | Assistant message with recommendation | Renders nested RecommendationCard |
| 4 | ChatInput | Enter key sends | Calls onSend with content |
| 5 | ChatInput | Shift+Enter adds newline | Does not call onSend |
| 6 | ChatInput | Disabled while streaming | Input disabled, button disabled |
| 7 | ToolStatusIndicator | Running state | Shows spinner + tool name |
| 8 | ToolStatusIndicator | Done state | Shows checkmark + summary |
| 9 | ThinkingIndicator | Renders | Shows animated dots |
| 10 | SessionCard | Displays info | Shows title, preview, date |
| 11 | SessionCard | Delete button | Calls onDelete |

### 8.2 Options Components
| # | Component | Test | Expected |
|---|-----------|------|----------|
| 1 | RecommendationCard | Header info | Shows strategy name, ticker, confidence badge, risk score |
| 2 | RecommendationCard | Accept button | Calls onDecision("accepted") |
| 3 | RecommendationCard | Reject button | Calls onDecision("rejected") |
| 4 | RecommendationCard | After decision | Buttons replaced with decision state |
| 5 | RecommendationCard | Risk flags shown | Displays relevant RiskFlagBadges |
| 6 | StrategyLegTable | Renders legs | Correct columns: Action, Type, Strike, Qty, Premium, Bid/Ask, IV, Greeks |
| 7 | StrategyLegTable | Buy leg styling | Green color for buy rows |
| 8 | StrategyLegTable | Sell leg styling | Red color for sell rows |
| 9 | RiskMetricsGrid | Displays all metrics | Max profit (green), max loss (red), breakevens, capital, margin, R:R |
| 10 | RiskMetricsGrid | Unlimited loss | Shows "Unlimited" instead of number |
| 11 | RiskFlagBadges | All flags | Renders: Unlimited Risk, Assignment Risk, High Gamma, Vol Sensitive |
| 12 | RiskFlagBadges | No flags | Renders nothing |
| 13 | RiskFlagBadges | Destructive style | Unlimited Risk badge uses destructive variant |

---

## 9. Frontend Hooks — Unit Tests

**File:** `frontend/src/hooks/__tests__/*.test.ts`
**Dependencies:** Vitest, mocked fetch

### 9.1 `useChat`
| # | Test | Expected |
|---|------|----------|
| 1 | sendMessage — adds optimistic user message | messages includes user msg immediately |
| 2 | sendMessage — sets isStreaming=true | isStreaming true during stream |
| 3 | SSE text event | streamingContent accumulates text chunks |
| 4 | SSE tool_start event | toolStatuses adds entry with status="running" |
| 5 | SSE tool_result event | toolStatuses entry updated to status="done" + summary |
| 6 | SSE recommendation event | pendingRecommendations includes recommendation object |
| 7 | SSE done event | Assistant message added to messages, streamingContent reset, isStreaming=false |
| 8 | SSE error event | Error message added to messages |
| 9 | Network failure | Error message added, isStreaming=false |
| 10 | Abort (component unmount) | No error message for AbortError |

### 9.2 `useSessions`
| # | Test | Expected |
|---|------|----------|
| 1 | useChatSessions fetches list | Returns sessions array |
| 2 | useCreateChatSession | POST called, cache invalidated |
| 3 | useDeleteChatSession | DELETE called, cache invalidated |

---

## 10. Live AI Integration Tests (real Anthropic API)

**File:** `backend/tests/test_ai_live.py`
**Dependencies:** Real Anthropic API key, mocked tool execution (no yfinance/DB calls)
**Run:** Separately via `pytest -m live` (marked with `@pytest.mark.live`)
**Note:** Non-deterministic. Tests assert tool selection, not exact text output.

### Setup
- Mock all tool handlers to return realistic fixture data
- Real Anthropic API call with real tool definitions
- Assert which tools Claude calls and with what arguments

### 10.1 Stock Tool Selection
| # | Prompt | Assert |
|---|--------|--------|
| 1 | "What's AAPL trading at?" | `get_stock_quote` called with ticker="AAPL" |
| 2 | "How's my portfolio doing?" | `get_portfolio_holdings` or `get_portfolio_summary` called |
| 3 | "Any recent news on Tesla?" | `get_stock_news` called with ticker="TSLA" |
| 4 | "Compare AAPL and MSFT prices" | `get_stock_quote` called 2+ times with both tickers |

### 10.2 Options Tool Selection
| # | Prompt | Assert |
|---|--------|--------|
| 5 | "What expiration dates are available for NVDA options?" | `get_options_expirations` called with ticker="NVDA" |
| 6 | "Show me the options chain for AAPL expiring 2026-04-17" | `get_options_chain` called (possibly after `get_options_expirations`) |
| 7 | "I'm bullish on TSLA, suggest a simple call option" | `generate_options_strategy` called with strategy_type in (long_call) and 1 leg |
| 8 | "Set up an iron condor on SPY" | `generate_options_strategy` called with strategy_type="iron_condor" and 4 legs |

### 10.3 Options Pipeline Verification
| # | Test | Assert |
|---|------|--------|
| 9 | Strategy recommendation emits recommendation event | stream_chat yields event with event="recommendation" |
| 10 | Recommendation contains server-computed Greeks | Legs in recommendation have delta/gamma/theta/vega (from quant engine, not hallucinated) |
| 11 | Recommendation contains server-computed risk | risk_score, max_profit, max_loss, breakevens present |

---

## Execution Order (priority)

1. **Quant engine + Risk engine** (Sections 1-2) — Pure unit tests, no mocking, highest confidence
2. **Options data service** (Section 3) — Mocked yfinance, tests filtering logic
3. **Tool handlers** (Section 4) — Integration tests, validates the enrichment pipeline
4. **Chat service** (Section 7) — DB persistence logic
5. **AI engine** (Section 5) — Streaming pipeline with mocked Anthropic
6. **Chat router** (Section 6) — API-level tests
7. **Frontend components** (Section 8) — UI rendering
8. **Frontend hooks** (Section 9) — SSE parsing logic
9. **Live AI tests** (Section 10) — Last, expensive, non-deterministic

## Test Counts

| Section | Tests |
|---------|-------|
| 1. Quant Engine | ~30 |
| 2. Risk Engine | 12 |
| 3. Options Data Service | 7 |
| 4. Tool Handlers | 25 |
| 5. AI Engine | 9 |
| 6. Chat Router | 14 |
| 7. Chat Service | 10 |
| 8. Frontend Components | 24 |
| 9. Frontend Hooks | 13 |
| 10. Live AI | 11 |
| **Total** | **~155** |
