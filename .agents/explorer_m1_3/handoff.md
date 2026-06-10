# Handoff Report: Database Schema Design

## 1. Observation
- Read the scope file at `c:/Users/Figue/Desktop/Paper Trading Antigravity/.agents/sub_orch_m1/SCOPE.md`.
- Architecture specifies `portfolio` for USD balances and asset quantities, and `trades` for trade history.
- The user requests an initial balance of 100,000 USD in `portfolio`.
- Interfaces defined:
  - Bot queries `portfolio` for USD balances and asset holdings.
  - Bot inserts trade records into `trades`.
  - Bot updates `portfolio` balance and asset holdings after trade.
  - Dashboard reads both tables.

## 2. Logic Chain
- The `portfolio` table needs to store arbitrary assets and their balances. A simple schema `(asset_symbol, balance, updated_at)` is optimal.
  - `asset_symbol`: `VARCHAR(10)` (e.g., 'USD', 'BTC', 'ETH'). Primary Key.
  - `balance`: `NUMERIC(18, 8)` to safely store crypto fractions and large dollar amounts.
  - `updated_at`: `TIMESTAMPTZ` for dashboard ordering/monitoring.
- The `trades` table tracks individual transactions.
  - `id`: `UUID` (defaulting to `gen_random_uuid()`) or `SERIAL`. UUID is preferred in Supabase.
  - `asset_symbol`: `VARCHAR(10)` (the traded asset).
  - `side`: `VARCHAR(4)` ('BUY' or 'SELL').
  - `quantity`: `NUMERIC(18, 8)`.
  - `price_usd`: `NUMERIC(18, 8)` (execution price per unit in USD).
  - `total_value_usd`: `NUMERIC(18, 8)` (can be calculated as `quantity * price_usd`, but good to store directly for simpler dashboard queries).
  - `timestamp`: `TIMESTAMPTZ` with `DEFAULT NOW()`.
- Initializing the 100,000 USD balance requires an `INSERT` statement into `portfolio` on setup.

## 3. Caveats
- `trades` schema doesn't currently reference `portfolio` via Foreign Key on `asset_symbol`, to avoid inserting zero-balance assets into `portfolio` just to satisfy FK constraints, or it can reference it if we ensure assets exist in `portfolio` before trading. For simplicity in paper trading, it's easier to omit the FK constraint on `asset_symbol` so `trades` acts as a pure log.
- Using `NUMERIC(18, 8)` handles up to 10 billion units with 8 decimal places. If larger figures are expected, precision might need increasing.

## 4. Conclusion
Proposed Schema:

```sql
-- Create portfolio table
CREATE TABLE portfolio (
    asset_symbol VARCHAR(10) PRIMARY KEY,
    balance NUMERIC(18, 8) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create trades table
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity NUMERIC(18, 8) NOT NULL,
    price_usd NUMERIC(18, 8) NOT NULL,
    total_value_usd NUMERIC(18, 8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Function to update 'updated_at' on portfolio
CREATE OR REPLACE FUNCTION update_portfolio_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update 'updated_at'
CREATE TRIGGER portfolio_updated_at_trigger
BEFORE UPDATE ON portfolio
FOR EACH ROW
EXECUTE FUNCTION update_portfolio_updated_at();

-- Initial balance setup
INSERT INTO portfolio (asset_symbol, balance)
VALUES ('USD', 100000.00);
```

## 5. Verification Method
- Review the handoff report against `SCOPE.md` requirements.
- Verify `portfolio` correctly captures USD and other asset balances via `asset_symbol` and `balance`.
- Verify `trades` captures history required for the dashboard.
- Verify the seed query allocates precisely 100,000 to 'USD'.
