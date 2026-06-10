# Database Schema Design Handoff

## 1. Observation
- `c:/Users/Figue/Desktop/Paper Trading Antigravity/.agents/sub_orch_m1/SCOPE.md` requires a Supabase PostgreSQL schema with two tables: `portfolio` and `trades`.
- `portfolio` tracks USD balances and asset quantities.
- `trades` tracks trade history.
- Interface contracts specify the bot will query/update `portfolio` and insert into `trades`.
- Objective requires proposing the schema and the setup script for an initial $100,000 USD balance in `portfolio`.
- Constraint: We are NOT to write actual files in the `/db` directory.

## 2. Logic Chain
- **Table `portfolio`**: Needs to store both the USD balance and various asset holdings. A flexible approach is to have a row per asset, using the `asset` ticker as a primary key (e.g., 'USD', 'BTC'). 
  - `asset` (VARCHAR): Unique identifier for the holding.
  - `quantity` (NUMERIC): Exact decimal representation of the balance. `NUMERIC` is required to prevent floating-point precision loss.
  - `updated_at` (TIMESTAMPTZ): Tracks when the balance was last updated.
- **Table `trades`**: Needs to record every executed transaction.
  - `id` (SERIAL/UUID): Unique trade identifier.
  - `symbol` (VARCHAR): Trading pair (e.g., 'BTC/USD').
  - `side` (VARCHAR): 'BUY' or 'SELL'.
  - `quantity` (NUMERIC): Amount of the base asset traded.
  - `price` (NUMERIC): Execution price in the quote asset.
  - `timestamp` (TIMESTAMPTZ): When the trade occurred.
- **Initial Setup**: An `INSERT` statement is needed to seed the `portfolio` table with 100,000 USD. The `ON CONFLICT` clause is useful to make the initialization script idempotent.

## 3. Caveats
- **User scope**: The schema assumes a single-user system (no `user_id` columns). If this expands to a multi-user platform, a `user_id` column must be added to both tables.
- **Short selling**: There is no `CHECK (quantity >= 0)` constraint on the `portfolio` table, meaning short positions (negative balances) are technically allowed at the DB level. If strict positive balances are required, a constraint should be added.
- **Precision**: `NUMERIC(24, 8)` is chosen for balances and prices to accommodate large fiat numbers and high-precision crypto fractions, but this can be adjusted if higher precision is needed.

## 4. Conclusion
The proposed schema and setup script are as follows:

```sql
-- Create portfolio table
CREATE TABLE portfolio (
    asset VARCHAR(20) PRIMARY KEY,
    quantity NUMERIC(24, 8) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trades table
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity NUMERIC(24, 8) NOT NULL,
    price NUMERIC(24, 8) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Initialize portfolio with 100,000 USD
INSERT INTO portfolio (asset, quantity) 
VALUES ('USD', 100000.00000000)
ON CONFLICT (asset) DO UPDATE SET quantity = EXCLUDED.quantity;
```

## 5. Verification Method
- **Syntax Check**: Execute the SQL commands in a local PostgreSQL or Supabase SQL Editor.
- **Validation**:
  - Run `SELECT * FROM portfolio;` to verify that the 'USD' row exists with a quantity of 100,000.
  - Attempt to insert a valid trade (`INSERT INTO trades (symbol, side, quantity, price) VALUES ('BTC/USD', 'BUY', 0.5, 60000);`) and verify it succeeds.
  - Attempt to insert an invalid trade side (`INSERT INTO trades (symbol, side, quantity, price) VALUES ('BTC/USD', 'HOLD', 0.5, 60000);`) and verify it is rejected by the `CHECK` constraint.
