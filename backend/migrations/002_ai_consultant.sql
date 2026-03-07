-- Phase 2: AI Investment Consultant

-- Chat sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_portfolio ON chat_sessions(portfolio_id);
CREATE INDEX idx_chat_sessions_updated ON chat_sessions(updated_at DESC);

-- Auto-update updated_at
CREATE TRIGGER set_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Chat messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    has_recommendation BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);

-- Options recommendations
CREATE TABLE options_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,

    -- Strategy
    strategy_type TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    confidence_score NUMERIC,

    -- AI reasoning
    strategy_reasoning TEXT,
    strike_reasoning TEXT,
    expiration_reasoning TEXT,
    entry_conditions TEXT,
    exit_conditions TEXT,
    adverse_scenario TEXT,

    -- Risk metrics
    max_profit NUMERIC,
    max_loss NUMERIC,
    breakeven_prices NUMERIC[],
    capital_required NUMERIC,
    margin_requirement NUMERIC,
    risk_reward_ratio NUMERIC,
    risk_score INTEGER CHECK (risk_score >= 1 AND risk_score <= 10),

    -- Risk flags
    has_unlimited_risk BOOLEAN NOT NULL DEFAULT FALSE,
    has_assignment_risk BOOLEAN NOT NULL DEFAULT FALSE,
    has_high_gamma BOOLEAN NOT NULL DEFAULT FALSE,
    has_volatility_sensitivity BOOLEAN NOT NULL DEFAULT FALSE,

    -- Market snapshot
    spot_price_at_analysis NUMERIC,
    expiration_date DATE,
    days_to_expiry INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_options_recommendations_session ON options_recommendations(session_id);
CREATE INDEX idx_options_recommendations_message ON options_recommendations(message_id);

-- Options recommendation legs
CREATE TABLE options_recommendation_legs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID NOT NULL REFERENCES options_recommendations(id) ON DELETE CASCADE,
    leg_order INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('buy', 'sell')),
    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
    strike NUMERIC NOT NULL,
    contracts INTEGER NOT NULL DEFAULT 1,
    premium NUMERIC,
    bid NUMERIC,
    ask NUMERIC,
    implied_volatility NUMERIC,
    open_interest INTEGER,
    volume INTEGER,
    delta NUMERIC,
    gamma NUMERIC,
    theta NUMERIC,
    vega NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_options_legs_recommendation ON options_recommendation_legs(recommendation_id);

-- Options decisions
CREATE TABLE options_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID NOT NULL REFERENCES options_recommendations(id) UNIQUE,
    decision TEXT NOT NULL CHECK (decision IN ('accepted', 'rejected')),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS (permissive for now)
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE options_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE options_recommendation_legs ENABLE ROW LEVEL SECURITY;
ALTER TABLE options_decisions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all on chat_sessions" ON chat_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on chat_messages" ON chat_messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on options_recommendations" ON options_recommendations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on options_recommendation_legs" ON options_recommendation_legs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on options_decisions" ON options_decisions FOR ALL USING (true) WITH CHECK (true);
