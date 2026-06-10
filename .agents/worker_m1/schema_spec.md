# Database Schema Specification

Based on Explorer consensus, implement the following PostgreSQL schema for Supabase:

## Tables

### 1. `portfolio`
- `asset_symbol` VARCHAR(10) PRIMARY KEY
- `balance` NUMERIC(24, 8) NOT NULL CHECK (balance >= 0)
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

### 2. `trades`
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `asset_symbol` VARCHAR(10) NOT NULL
- `trade_type` VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY', 'SELL'))
- `quantity` NUMERIC(24, 8) NOT NULL CHECK (quantity > 0)
- `price_usd` NUMERIC(24, 8) NOT NULL CHECK (price_usd > 0)
- `total_value_usd` NUMERIC(24, 8) NOT NULL CHECK (total_value_usd > 0)
- `executed_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

## Triggers
- Create a `plpgsql` function and trigger to auto-update `portfolio.updated_at` on `UPDATE`.

## Seeding
- Insert the initial balance: `INSERT INTO portfolio (asset_symbol, balance) VALUES ('USD', 100000.00) ON CONFLICT (asset_symbol) DO UPDATE SET balance = EXCLUDED.balance;`

## Instructions
- Create the `/db` directory if it doesn't exist.
- Write the combined DDL and DML to `c:/Users/Figue/Desktop/Paper Trading Antigravity/db/init.sql`.
- Ensure it is a complete, syntactically correct PostgreSQL script.
