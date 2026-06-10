# Schema Design Handoff

## 1. Observation
- `c:/Users/Figue/Desktop/Paper Trading Antigravity/.agents/sub_orch_m1/SCOPE.md` specifies a Supabase PostgreSQL architecture with two primary tables: `portfolio` (for USD balances and asset quantities) and `trades` (for trade history).
- The Bot interface requires querying and updating `portfolio` and inserting into `trades`.
- The Dashboard interface requires reading from both tables to display current state and history.
- The user request explicitly requires a schema proposal for these two tables along with constraints, data types, rationale, and a setup script to initialize a 100,000 USD balance.
- Boundary constraint: No files should be written to the `/db` directory yet.

## 2. Logic Chain
- **Table Structure:**
  - `portfolio`: Needs to track arbitrary assets. The most flexible design is a table where each row represents an asset (e.g., 'USD', 'AAPL') and its current quantity. Thus, `asset_symbol` serves perfectly as the Primary Key.
  - `trades`: Must act as an immutable ledger. It needs a unique identifier (UUID), the asset involved, the direction (`BUY` or `SELL`), the amount traded (`quantity`), the price (`price_per_unit`), and the total cash impact (`total_value`). The time of execution is also critical (`executed_at`).
- **Data Types:** Financial data (balances, prices) must avoid floating-point inaccuracies. PostgreSQL's `NUMERIC` type provides arbitrary precision and is standard for this use case.
- **Constraints:** 
  - `trade_type` must be strictly validated.
  - Quantities and prices in `trades` must be strictly positive to ensure data integrity.
  - A `CHECK (quantity >= 0)` constraint on the `portfolio` table ensures the bot doesn't accidentally execute trades resulting in a negative balance or short-selling, enforcing basic safety logic at the DB level.

## 3. Caveats
- **Single User Context**: The schema assumes a single-portfolio architecture without a `user_id` column. If this application ever scales to multi-user, an `account_id` or `user_id` will need to be added to the primary keys/foreign keys.
- **Short Selling / Margin**: The `CHECK (quantity >= 0)` constraint on `portfolio` strictly forbids short-selling assets or overdrawing the USD cash balance. If shorting or margin features are planned, this constraint must be removed.
- **Foreign Keys**: Currently, `trades.asset_symbol` does not have a foreign key constraint referencing `portfolio.asset_symbol` because a user might sell an asset entirely (removing the row or setting it to 0), or we might want to log a trade without strictly requiring the asset row to exist prior. 

## 4. Conclusion
Below is the proposed schema, constraints, data types, and initialization script.

### Proposed Schema

```sql
-- Portfolio Table
CREATE TABLE portfolio (
    asset_symbol VARCHAR(10) PRIMARY KEY,
    quantity NUMERIC NOT NULL CHECK (quantity >= 0),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trades Table
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_symbol VARCHAR(10) NOT NULL,
    trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    quantity NUMERIC NOT NULL CHECK (quantity > 0),
    price_per_unit NUMERIC NOT NULL CHECK (price_per_unit > 0),
    total_value NUMERIC NOT NULL CHECK (total_value > 0),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Initial Balance Setup Script
```sql
INSERT INTO portfolio (asset_symbol, quantity) 
VALUES ('USD', 100000.00);
```

## 5. Verification Method
- **Syntax Check**: Start a PostgreSQL or local Supabase instance, execute the DDL, and ensure no syntax errors.
- **Seed Check**: Execute the `INSERT` script and run `SELECT * FROM portfolio;` to verify that exactly 1 row with `asset_symbol = 'USD'` and `quantity = 100000.00` exists.
- **Constraint Test**: Attempt to insert a trade with `trade_type = 'HOLD'` or `quantity = -5`. Ensure the database rejects it with a constraint violation error. Attempt to update the 'USD' portfolio row to `-100`, which should similarly fail.
