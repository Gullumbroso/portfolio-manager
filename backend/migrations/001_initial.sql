-- Portfolio Manager: Initial Schema
-- Run this in the Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLES
-- =============================================================================

CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL')),
    ticker TEXT,  -- NULL for DEPOSIT/WITHDRAWAL
    shares NUMERIC,  -- NULL for DEPOSIT/WITHDRAWAL
    price_per_share NUMERIC,  -- NULL for DEPOSIT/WITHDRAWAL
    amount NUMERIC NOT NULL,  -- Total dollar amount of the transaction
    note TEXT DEFAULT '',
    transacted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE price_cache (
    ticker TEXT PRIMARY KEY,
    price NUMERIC NOT NULL,
    change_amount NUMERIC DEFAULT 0,
    change_percent NUMERIC DEFAULT 0,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_value NUMERIC NOT NULL,
    cash_balance NUMERIC NOT NULL,
    market_value NUMERIC NOT NULL,
    total_deposits NUMERIC NOT NULL,
    profit NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (portfolio_id, date)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id);
CREATE INDEX idx_transactions_portfolio_ticker ON transactions(portfolio_id, ticker);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_transacted_at ON transactions(transacted_at);
CREATE INDEX idx_snapshots_portfolio_date ON portfolio_snapshots(portfolio_id, date);
CREATE INDEX idx_price_cache_fetched ON price_cache(fetched_at);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Holdings view: derives current holdings from transaction log
CREATE OR REPLACE VIEW holdings_view AS
SELECT
    portfolio_id,
    ticker,
    SUM(CASE WHEN type = 'BUY' THEN shares ELSE 0 END) -
        SUM(CASE WHEN type = 'SELL' THEN shares ELSE 0 END) AS total_shares,
    SUM(CASE WHEN type = 'BUY' THEN amount ELSE 0 END) AS total_cost_basis,
    SUM(CASE WHEN type = 'SELL' THEN amount ELSE 0 END) AS total_sell_proceeds
FROM transactions
WHERE ticker IS NOT NULL
GROUP BY portfolio_id, ticker
HAVING (SUM(CASE WHEN type = 'BUY' THEN shares ELSE 0 END) -
        SUM(CASE WHEN type = 'SELL' THEN shares ELSE 0 END)) > 0;

-- Portfolio cash view: derives cash balance from transaction log
CREATE OR REPLACE VIEW portfolio_cash_view AS
SELECT
    portfolio_id,
    SUM(CASE WHEN type = 'DEPOSIT' THEN amount ELSE 0 END) -
        SUM(CASE WHEN type = 'WITHDRAWAL' THEN amount ELSE 0 END) AS total_external_deposits,
    SUM(CASE WHEN type = 'DEPOSIT' THEN amount ELSE 0 END) +
        SUM(CASE WHEN type = 'SELL' THEN amount ELSE 0 END) -
        SUM(CASE WHEN type = 'BUY' THEN amount ELSE 0 END) -
        SUM(CASE WHEN type = 'WITHDRAWAL' THEN amount ELSE 0 END) AS cash_balance
FROM transactions
GROUP BY portfolio_id;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at on portfolios
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_portfolios_updated_at
    BEFORE UPDATE ON portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (optional, for Supabase auth later)
-- =============================================================================

ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_snapshots ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (no auth yet)
CREATE POLICY "Allow all on portfolios" ON portfolios FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on transactions" ON transactions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on price_cache" ON price_cache FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on portfolio_snapshots" ON portfolio_snapshots FOR ALL USING (true) WITH CHECK (true);
