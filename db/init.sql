-- Create portfolio table
CREATE TABLE IF NOT EXISTS portfolio (
    asset_symbol VARCHAR(10) PRIMARY KEY,
    balance NUMERIC(24, 8) NOT NULL CHECK (balance >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_symbol VARCHAR(10) NOT NULL,
    trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    quantity NUMERIC(24, 8) NOT NULL CHECK (quantity > 0),
    price_usd NUMERIC(24, 8) NOT NULL CHECK (price_usd > 0),
    total_value_usd NUMERIC(24, 8) NOT NULL CHECK (total_value_usd > 0),
    ai_justification TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update portfolio.updated_at on UPDATE
DROP TRIGGER IF EXISTS trigger_portfolio_updated_at ON portfolio;
CREATE TRIGGER trigger_portfolio_updated_at
    BEFORE UPDATE ON portfolio
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Seed initial USD balance
INSERT INTO portfolio (asset_symbol, balance)
VALUES ('USD', 100000.00)
ON CONFLICT (asset_symbol) DO UPDATE SET balance = EXCLUDED.balance;
